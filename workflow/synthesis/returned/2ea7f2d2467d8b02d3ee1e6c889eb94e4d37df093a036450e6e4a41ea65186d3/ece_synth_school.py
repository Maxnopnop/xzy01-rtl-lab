"""Python 3.6+ ECE desktop: ONE selected synthesis package, collect, ship."""
import argparse
import datetime
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import uuid
import zipfile

from ece_synth_common import TOOLS, INPUTS, ARTIFACTS, REQUIRED, read, save, sha, verify, extract, copy_once, validate_profile


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]


def doctor(root):
    job = verify(root)
    profile = job['profile']
    missing = validate_profile(job['tool'], profile)
    libraries = []
    for path in profile['libraries']:
        item = dict(path=path, readable=False)
        try:
            if not Path(path).is_file(): raise OSError('Not a regular file')
            item.update(readable=True, sha256=sha(Path(path)), bytes=Path(path).stat().st_size)
        except OSError:
            missing.append('unreadable library: ' + path)
        libraries.append(item)
    setup = Path(TOOLS[job['tool']]['setup'])
    if not setup.is_file(): missing.append('setup script')
    if not shutil.which('tcsh'): missing.append('tcsh')
    if os.name != 'posix': missing.append('school Linux host')
    if not (root / 'constraints.sdc').read_bytes().strip(): missing.append('nonempty SDC')
    return dict(tool=job['tool'], expected_version=TOOLS[job['tool']]['version'],
        host=os.uname().nodename if os.name == 'posix' else 'LOCAL_WINDOWS',
        setup=str(setup), setup_sha256=sha(setup) if setup.is_file() else None,
        libraries=libraries, corner=profile['corner'], sdc_sha256=job['sdc_sha256'],
        missing=missing, status='READY_FOR_ONE_MANUAL_RUN' if not missing else 'BLOCKED_PREREQUISITES',
        license='Not checked; no tool started by doctor')


def run(root):
    job = verify(root)
    # Refuse accidental repeat; a fresh menu selection creates a fresh directory.
    if (root / 'execution.json').exists():
        raise ValueError('Existing attempt; use ship to resend without rerunning synthesis')
    # Exclusive reservation closes the double-click/concurrent invocation race.
    with (root / '.run-reserved').open('x') as reservation:
        reservation.write(str(os.getpid()))
    record = dict(package_id=job['package_id'], nonce=job['nonce'], tool=job['tool'],
                  started=stamp(), status='STARTED', returncode=None)
    save(root / 'execution.json', record)
    check = doctor(root)
    save(root / 'doctor.json', check)
    if check['missing']:
        record.update(status='BLOCKED_PREREQUISITES', missing=check['missing'], finished=stamp())
        save(root / 'execution.json', record)
        print('No synthesis started. Missing: ' + ', '.join(check['missing']))
        return 2
    with (root / 'tool.log').open('wb') as log:
        try:
            process = subprocess.Popen(['tcsh', '-f', str(root / 'launch.csh')], cwd=str(root),
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as exc:
            record.update(status='ENV_ERROR', error=type(exc).__name__, finished=stamp())
            save(root / 'execution.json', record)
            return 2
        try:
            record['returncode'] = process.wait(timeout=job['profile']['timeout_seconds'])
            record['status'] = 'EXITED'
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            record.update(returncode=process.returncode, status='TIMEOUT' if isinstance(exc, subprocess.TimeoutExpired) else 'INTERRUPTED')
    record['finished'] = stamp()
    save(root / 'execution.json', record)
    return 0 if record['status'] == 'EXITED' and record['returncode'] == 0 else 1


def collect(root):
    job = verify(root)
    read(root / 'execution.json')
    name = 'return-synth-' + stamp()
    output = root / 'outbox'
    output.mkdir(exist_ok=True)
    paths = [root / name for name in sorted(INPUTS | ARTIFACTS | {'payload-lock.json'}) if (root / name).is_file()]
    if any(path.is_symlink() for path in paths) or sum(path.stat().st_size for path in paths) > 100 * 1024 ** 2:
        raise ValueError('Return too large or contains symlinks; evidence retained in school HOME')
    with zipfile.ZipFile(output / (name + '.zip'), 'x', zipfile.ZIP_DEFLATED) as archive:
        for path in paths: archive.write(str(path), path.relative_to(root).as_posix())
    save(output / (name + '.json'), dict(kind='synthesis', package_id=job['package_id'],
        archive=name + '.zip', archive_sha256=sha(output / (name + '.zip')),
        input_lock_sha256=sha(root / 'payload-lock.json')))


def ship(root, destination):
    for sidecar in sorted((root / 'outbox').glob('return-synth-*.json')):
        data = read(sidecar)
        if Path(data['archive']).name != data['archive']:
            raise ValueError('Invalid archive path')
        source = sidecar.parent / data['archive']
        if sha(source) != data['archive_sha256']: raise ValueError('Return ZIP changed')
        copy_once(source, destination / source.name)
        copy_once(sidecar, destination / sidecar.name)
    print('Return copied; no synthesis started by ship.')


def menu(shared, package_id=None, work=None, return_dir=None):
    rows = read(shared / 'synthesis-catalog.json')['packages']
    if not rows: raise ValueError('No synthesis packages; prepare one in the local control window')
    print('ONE manually selected synthesis design. No SSH, scheduler or multi-case loop.')
    if package_id:
        selected = [r for r in rows if r['package_id'] == package_id]
        if len(selected) != 1: raise ValueError('Select one exact package ID')
        item = selected[0]
    else:
        for i, row in enumerate(rows):
            print('%d. %s | %s | %s' % (i + 1, row['tool'], row['job_id'], row['readiness']))
        answer = input('Select one number (Enter cancels): ').strip()
        if not answer: return 0
        if not answer.isdigit() or not 1 <= int(answer) <= len(rows): raise ValueError('Invalid selection')
        item = rows[int(answer) - 1]
    if Path(item['archive']).name != item['archive']:
        raise ValueError('Unsafe package filename')
    archive = shared / item['archive']
    if sha(archive) != item['archive_sha256']: raise ValueError('Package archive changed')
    target = (work or Path.home() / 'xzy01-synthesis') / ('session-' + stamp())
    extract(archive, target, INPUTS | {'payload-lock.json'})
    job = verify(target)
    if job['package_id'] != item['package_id']: raise ValueError('Package ID mismatch')
    destination = return_dir or shared / 'inbox'
    print('School attempt: ' + str(target))
    # Execute the frozen runner packaged with this exact attempt.
    return subprocess.call([sys.executable, str(target / 'ece_synth_school.py'), 'session',
                            '--package', str(target), '--return-dir', str(destination)])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['menu', 'doctor', 'session', 'ship'], nargs='?', default='menu')
    parser.add_argument('--shared-dir', default=str(Path(__file__).resolve().parent))
    parser.add_argument('--package')
    parser.add_argument('--package-id')
    parser.add_argument('--return-dir')
    args = parser.parse_args(argv)
    try:
        if args.command == 'menu':
            return menu(Path(args.shared_dir).resolve(), args.package_id,
                        return_dir=Path(args.return_dir).resolve() if args.return_dir else None)
        if not args.package: raise ValueError('--package is required')
        root = Path(args.package).resolve()
        if args.command == 'doctor':
            import json
            result = doctor(root)
            print(json.dumps(result, indent=2))
            return 2 if result['missing'] else 0
        if not args.return_dir: raise ValueError('--return-dir is required')
        code = 0
        if args.command == 'session':
            code = run(root)
            collect(root)
        try:
            ship(root, Path(args.return_dir).resolve())
        except OSError:
            print('Return not copied. Evidence remains at: ' + str(root))
            print('Retry transfer only: python3 ece_synth_school.py ship --package "' + str(root) + '" --return-dir "' + args.return_dir + '"')
            return 2
        return code
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print('ERROR: ' + str(exc))
        return 2
    except (KeyboardInterrupt, EOFError):
        print('Selection cancelled')
        return 130


if __name__ == '__main__':
    sys.exit(main())
