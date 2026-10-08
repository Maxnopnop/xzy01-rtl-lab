"""Portable Python 3.6+ helper. Each run executes exactly one ECE case."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import uuid
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    lock = json.loads((root / 'transfer-lock.json').read_text(encoding='utf-8'))
    for name, expected in lock.items():
        path = root / name
        if path.is_symlink() or digest(path) != expected:
            raise ValueError('Package changed: ' + name)
    return json.loads((root / 'package.json').read_text(encoding='utf-8'))


def case_meta(root, case):
    package = verify(root)
    matches = [m for m in package['cases'] if m['job_id'] == case]
    if len(matches) != 1:
        raise ValueError('Select one exact case ID from list')
    return matches[0]


def run_case(root, case, timeout=300):
    meta = case_meta(root, case)
    if os.name != 'posix':
        raise ValueError('Run inside the ECE Linux desktop terminal')
    if not shutil.which('tcsh'):
        raise ValueError('tcsh unavailable; no simulation submitted')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    target = root / 'results' / case / stamp
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(root / case), str(target))
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = dict(case=case, backend=meta['backend'], started_utc=started, status='STARTED')
    (target / 'execution.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    with (target / 'launcher.log').open('wb') as log:
        process = subprocess.Popen(['tcsh', str(target / ('run_' + meta['backend'] + '.csh'))],
                                   cwd=str(target), stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            record['returncode'] = process.wait(timeout=timeout)
            record['status'] = 'EXITED'
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            record['status'] = 'TIMEOUT' if isinstance(exc, subprocess.TimeoutExpired) else 'INTERRUPTED'
            record['returncode'] = process.returncode
    record['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (target / 'execution.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print('Saved attempt: ' + str(target))
    return 0 if record['returncode'] == 0 and record['status'] == 'EXITED' else 1


def collect(root, case, attempt, output):
    meta = case_meta(root, case)
    folder = root / 'results' / case / attempt
    if Path(attempt).name != attempt or not folder.is_dir():
        raise ValueError('Use the exact saved attempt directory name')
    names = list(meta['hashes']) + ['case.json', 'execution.json', 'launcher.log',
            'tool_version.log', 'compile.log', 'simulate.log', 'xrun.log',
            'compile.exit', 'simulate.exit', 'verdict.txt']
    for name, expected in meta['hashes'].items():
        if digest(folder / name) != expected:
            raise ValueError('Attempt source changed: ' + name)
    if not (folder / 'execution.json').is_file():
        raise ValueError('Attempt has no execution record')
    with zipfile.ZipFile(str(output), 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            source = folder / name
            if source.is_file() and not source.is_symlink():
                archive.write(str(source), case + '/' + name)
    print('Return ZIP: ' + str(output))


def doctor(root):
    package = verify(root)
    env, default = ('VCS_SETUP', '/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc') if package['backend'] == 'vcs' else ('XCELIUM_SETUP', '/usr/eelocal/cadence/xcelium2303hf/.cshrc')
    setup = Path(os.environ.get(env, default))
    print(json.dumps(dict(platform=os.name, tcsh=shutil.which('tcsh'), setup=str(setup),
                         setup_exists=setup.is_file(), shared_folder_candidate=str(Path.home() / 'tsclient'),
                         shared_folder_exists=(Path.home() / 'tsclient').is_dir(),
                         policy='Manual ONE case per run; no SSH, scheduler or EDA batch.'), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parent))
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('list'); sub.add_parser('doctor')
    run = sub.add_parser('run'); run.add_argument('--case', required=True); run.add_argument('--timeout', type=int, default=300)
    col = sub.add_parser('collect'); col.add_argument('--case', required=True); col.add_argument('--attempt', required=True); col.add_argument('--out', required=True)
    args = parser.parse_args(); root = Path(args.root).resolve()
    try:
        if args.command == 'run':
            if not 1 <= args.timeout <= 3600: raise ValueError('Timeout must be 1..3600 seconds')
            return run_case(root, args.case, args.timeout)
        if args.command == 'collect': collect(root, args.case, args.attempt, Path(args.out))
        elif args.command == 'doctor': doctor(root)
        else:
            for meta in verify(root)['cases']:
                print(meta['job_id'] + ' | ' + meta['task'] + ' | local=' + meta['original_status'])
    except (ValueError, OSError, KeyError) as exc:
        print('ERROR: ' + str(exc)); return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
