"""ELEC5550 school helper: fetch once, select ONE design, return evidence."""
import argparse
import datetime
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
import zipfile

from elec_common import read, save, sha, copy_once, extract, relative, single_design

COURSE = '/staff/ee/dept/public/elec5550/ELEC5550_Lab.zip'
SETUPS = dict(dc='/usr/eelocal/synopsys/syn-vv2023.12/.cshrc',
              pt='/usr/eelocal/synopsys/pts-vt2022.03-sp5/.cshrc',
              pnr='/usr/eelocal/cadence/innovus201/.cshrc')


def stamp():
    return datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]


def doctor():
    return dict(host=os.uname().nodename if os.name == 'posix' else 'LOCAL_TEST',
        platform=os.name, python=sys.version.split()[0],
        executables={n: shutil.which(n) for n in ('bash', 'tcsh', 'git')},
        setup_exists={k: Path(p).is_file() for k, p in SETUPS.items()},
        policy='ONE manually selected design per invocation; no SSH or scheduler')


def fetch(shared, source=Path(COURSE)):
    if not source.is_file():
        raise ValueError('Course archive unavailable: ' + str(source))
    digest = sha(source)
    target = shared / 'intake' / ('course-' + digest + '.zip')
    copy_once(source, target)
    save(shared / 'intake' / 'course.json', dict(archive=target.name, sha256=digest, doctor=doctor()))
    print('Course archive copied to shared intake. No EDA tool was started.')
    print(str(target))


def tool_stage(stage, folder, output, timeout):
    """Load .cshrc in tcsh, then run the provided script in bash."""
    script = 'run_dc.sh' if stage == 'dc' else 'run.sh'
    launcher = output / (stage + '-launch.csh')
    lines = ['#!/bin/tcsh -f', 'source ' + SETUPS[stage], 'if ( $status != 0 ) exit 90']
    if stage == 'dc':
        lines += ['source ' + SETUPS['pt'], 'if ( $status != 0 ) exit 91']
    # Source the course script as required by the lab; cwd is passed separately.
    lines += ["exec bash -c 'source ./" + script + "'"]
    launcher.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    started = stamp()
    with (output / (stage + '.log')).open('wb') as log:
        proc = subprocess.Popen(['tcsh', '-f', str(launcher)], cwd=str(folder),
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        status = 'EXITED'
        try:
            code = proc.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            status = 'TIMEOUT' if isinstance(exc, subprocess.TimeoutExpired) else 'INTERRUPTED'
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            code = proc.returncode
    return dict(stage=stage, status=status, returncode=code, started=started, finished=stamp())


def ship(session, shared):
    for manifest in sorted((session / 'outbox').glob('*.json')):
        info = read(manifest)
        name = info['archive']
        if Path(name).name != name:
            raise ValueError('Invalid return name')
        source = manifest.parent / name
        if sha(source) != info['sha256']:
            raise ValueError('Outbox archive changed')
        copy_once(source, shared / 'inbox' / name)
        copy_once(manifest, shared / 'inbox' / manifest.name)
    print('Return transfer complete; no EDA tools started by ship.')


def collect(session, shared):
    info = read(session / 'execution.json')
    job = read(session / 'job.json')
    course = session / 'course' / str(relative(job['course_root']))
    chosen = []
    omitted = []
    suffixes = {'.rpt', '.txt', '.log', '.png', '.jpg', '.jpeg', '.gif', '.sdc', '.v', '.sv'}
    for stage in ('dc_release', 'innovus_release'):
        base = course / 'Flow' / stage
        # The lab says each design's reports/results live below Flow/<stage>/<design>.
        design = base / job['design']
        if design.is_dir():
            for p in sorted(design.rglob('*')):
                if p.is_file() and not p.is_symlink():
                    name = p.relative_to(course).as_posix()
                    if p.suffix.lower() in suffixes and p.stat().st_size <= 64 * 1024 ** 2:
                        chosen.append((p, 'artifacts/' + name))
                    else:
                        omitted.append(name)
    screenshots = session / 'screenshots'
    screenshots.mkdir(exist_ok=True)
    for p in sorted(screenshots.iterdir()):
        if p.is_file() and not p.is_symlink() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif'}:
            if p.stat().st_size <= 64 * 1024 ** 2:
                chosen.append((p, 'screenshots/' + p.name))
    for name in ('execution.json', 'job.json', 'doctor.json', 'dc.log', 'pnr.log', 'changes.json'):
        p = session / name
        if p.is_file():
            chosen.append((p, name))
    if sum(p.stat().st_size for p, _ in chosen) > 512 * 1024 ** 2:
        raise ValueError('Return exceeds 512 MiB; original results remain in school HOME')
    outbox = session / 'outbox'
    outbox.mkdir(exist_ok=True)
    name = 'elec-return-' + stamp()
    target = outbox / (name + '.zip')
    with zipfile.ZipFile(str(target), 'x', zipfile.ZIP_DEFLATED) as z:
        for path, arcname in chosen:
            z.write(str(path), arcname)
    metadata = dict(schema=1, archive=target.name, sha256=sha(target), job_id=job['job_id'],
        job_sha256=sha(session / 'job.json'), source_sha256=job['source_sha256'],
        session_id=info['session_id'], files={name: sha(p) for p, name in chosen}, omitted=omitted)
    save(outbox / (name + '.json'), metadata)
    print('Evidence retained in: ' + str(session))
    print('Put post-route screenshots in: ' + str(screenshots))
    print('Recollect without rerunning EDA: python3 elec_school.py collect --session "' + str(session) + '" --shared-dir "' + str(shared) + '"')
    try:
        ship(session, shared)
    except (ValueError, OSError) as exc:
        print('Transfer pending; outbox is preserved: ' + str(exc))
        return 2
    return 0


def execute(shared, entry, work, timeout=3600):
    jobfile = shared / 'jobs' / (entry['job_id'] + '.json')
    if sha(jobfile) != entry['sha256']:
        raise ValueError('Job configuration hash mismatch')
    job = read(jobfile)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', job['design']):
        raise ValueError('Invalid design identifier')
    if os.name != 'posix' or not shutil.which('tcsh'):
        raise ValueError('Use the school Linux desktop with tcsh')
    if not all(Path(path).is_file() for path in SETUPS.values()):
        raise ValueError('Required tool setup missing; inspect doctor output')
    archive = shared / 'sources' / (job['source_sha256'] + '.zip')
    if sha(archive) != job['source_sha256']:
        raise ValueError('Source archive hash mismatch')
    work.mkdir(parents=True, exist_ok=True)
    session = Path(tempfile.mkdtemp(prefix='elec-', dir=str(work))).resolve()
    shutil.copyfile(str(jobfile), str(session / 'job.json'))
    save(session / 'doctor.json', doctor())
    extract(archive, session / 'course')
    course = session / 'course' / str(relative(job['course_root']))
    changes = []
    for target, expected in job['overrides'].items():
        path = relative(target)
        source = shared / 'overrides' / job['job_id'] / str(path)
        if sha(source) != expected:
            raise ValueError('Override hash mismatch')
        original = course / str(path)
        changes.append(dict(path=target, before=sha(original), after=expected))
        shutil.copyfile(str(source), str(original))
    for stage in ('dc_release', 'innovus_release'):
        single_design(course / 'Flow' / stage / 'list_design', job['design'])
    save(session / 'changes.json', changes)
    info = dict(schema=1, session_id=session.name, job_id=job['job_id'], stages=[],
                status='STARTED', design=job['design'], variant=job['variant'])
    save(session / 'execution.json', info)
    print('Running one design: ' + job['design'] + ' / ' + job['variant'], flush=True)
    print('School working copy: ' + str(course), flush=True)
    for stage, folder in (('dc', 'dc_release'), ('pnr', 'innovus_release')):
        try:
            row = tool_stage(stage, course / 'Flow' / folder, session, timeout)
        except OSError as exc:
            row = dict(stage=stage, status='ENV_ERROR', error=type(exc).__name__, returncode=None)
        info['stages'].append(row)
        save(session / 'execution.json', info)
        if row['status'] != 'EXITED' or row['returncode'] != 0:
            break
    info['status'] = ('FLOW_EXITED_NOT_VERIFIED' if len(info['stages']) == 2 and
        all(s['status'] == 'EXITED' and s['returncode'] == 0 for s in info['stages']) else 'FLOW_ERROR')
    save(session / 'execution.json', info)
    code = collect(session, shared)
    return code or (0 if info['status'] == 'FLOW_EXITED_NOT_VERIFIED' else 1)


def menu(shared, work):
    entries = read(shared / 'catalog.json')['jobs']
    print('Select ONE design/variant; 0 exits. No multi-design batch.')
    for i, row in enumerate(entries, 1):
        print(str(i) + '. ' + row['design'] + ' / ' + row['variant'])
    answer = input('Number: ').strip()
    if answer == '0':
        return 0
    if not answer.isdigit() or not 1 <= int(answer) <= len(entries):
        raise ValueError('Invalid selection')
    return execute(shared, entries[int(answer) - 1], work)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', default='menu', choices=['fetch', 'doctor', 'menu', 'collect', 'ship'])
    parser.add_argument('--shared-dir', default=str(Path(__file__).resolve().parent))
    parser.add_argument('--source', default=COURSE)
    parser.add_argument('--work-dir', default=str(Path.home() / 'elec5550-work'))
    parser.add_argument('--session')
    args = parser.parse_args()
    shared = Path(args.shared_dir).resolve()
    try:
        if args.command == 'fetch':
            fetch(shared, Path(args.source))
        elif args.command == 'doctor':
            print(doctor())
        elif args.command == 'menu':
            if not (shared / 'catalog.json').exists():
                fetch(shared, Path(args.source))
                print('First-time intake complete. Prepare jobs on the local computer, then run this same command again.')
            else:
                return menu(shared, Path(args.work_dir))
        else:
            if not args.session:
                raise ValueError('--session is required')
            session = Path(args.session).resolve()
            return collect(session, shared) if args.command == 'collect' else ship(session, shared)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print('ERROR: ' + str(exc))
        return 2
    except (KeyboardInterrupt, EOFError):
        return 130
    return 0


if __name__ == '__main__':
    sys.exit(main())
