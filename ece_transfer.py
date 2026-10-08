"""Local ECE package, staging and verified result import. No remote execution."""
import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile
import ece_desktop
import school_bridge


def pack(run, output, backend, jobs):
    if output.exists() or output.with_suffix('.zip').exists():
        raise ValueError('Use a new package name')
    school_bridge.export(run, output, backend, jobs)
    for name in ('ece_desktop.py', 'ECE_DESKTOP_GUIDE.md'):
        shutil.copyfile(Path(__file__).parent / name, output / name)
    lock = {p.relative_to(output).as_posix(): ece_desktop.digest(p)
            for p in output.rglob('*') if p.is_file()}
    (output / 'transfer-lock.json').write_text(json.dumps(lock, indent=2), encoding='utf-8')
    archive = output.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for p in output.rglob('*'):
            if p.is_file(): z.write(p, output.name + '/' + p.relative_to(output).as_posix())
    print('Package ZIP: ' + str(archive)); return archive


def stage(archive, shared):
    shared.mkdir(parents=True, exist_ok=True)
    target = shared / archive.name
    with archive.open('rb') as source, target.open('xb') as dest:
        shutil.copyfileobj(source, dest)
    if ece_desktop.digest(target) != ece_desktop.digest(archive):
        raise ValueError('Transfer hash mismatch')
    print('Share this dedicated folder in Horizon: ' + str(shared))


def extract_return(archive, destination, package):
    if destination.exists(): raise ValueError('Use a new returned directory')
    allowed = set()
    for meta in package['cases']:
        for name in list(meta['hashes']) + ['case.json','execution.json','launcher.log','tool_version.log',
                'compile.log','simulate.log','xrun.log','compile.exit','simulate.exit','verdict.txt']:
            allowed.add(meta['job_id'] + '/' + name)
    with zipfile.ZipFile(archive) as z:
        members = z.infolist(); seen = set()
        if len(members) > 5000 or sum(m.file_size for m in members) > 100 * 1024 * 1024:
            raise ValueError('Return ZIP exceeds limits')
        for member in members:
            name = member.filename
            if name not in allowed or name in seen or '\\' in name or ':' in name or '..' in PurePosixPath(name).parts or stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError('Unsafe or unexpected ZIP member: ' + name)
            seen.add(name)
        destination.mkdir(parents=True)
        for member in members:
            target = destination / member.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(member) as source, target.open('xb') as dest:
                shutil.copyfileobj(source, dest)


def receive(package_dir, archive, destination):
    package = ece_desktop.verify(package_dir)
    extract_return(archive, destination, package)
    rows = school_bridge.import_results(package_dir, destination)
    for row in rows:
        if not (destination / row['job_id']).exists():
            row.update(status='NOT_RUN', message='No case returned; not verified')
            continue
        record = destination / row['job_id'] / 'execution.json'
        if record.exists():
            execution = json.loads(record.read_text(encoding='utf-8'))
            if execution.get('status') in ('STARTED', 'TIMEOUT', 'INTERRUPTED'):
                row.update(status='SIM_ERROR', message='Incomplete launcher execution: ' + execution['status'])
            elif execution.get('returncode') != 0 and row['status'] in ('PASS','NOT_RUN'):
                row.update(status='ENV_ERROR', message='Launcher failed; inspect launcher.log')
            elif execution.get('status') != 'EXITED':
                row.update(status='EVIDENCE_ERROR', message='Invalid execution record')
        else:
            row.update(status='EVIDENCE_ERROR', message='Missing execution record; use legacy import for manual fallback')
    report = dict(results=rows, note='User-returned evidence; no remote host attestation. Missing cases remain unverified.')
    (destination / 'import-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    # Keep both report locations consistent after launcher-level checks.
    (package_dir / 'commercial_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if all(r['status'] == 'PASS' for r in rows) else 1


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('pack'); a.add_argument('--run-dir', required=True); a.add_argument('--out', required=True); a.add_argument('--backend', choices=('vcs','xcelium'), required=True); a.add_argument('--jobs', required=True)
    a = sub.add_parser('stage'); a.add_argument('--zip', required=True); a.add_argument('--shared-dir', required=True)
    a = sub.add_parser('receive'); a.add_argument('--package', required=True); a.add_argument('--zip', required=True); a.add_argument('--out', required=True)
    args = p.parse_args()
    try:
        if args.command == 'pack': pack(Path(args.run_dir).resolve(), Path(args.out).resolve(), args.backend, args.jobs)
        elif args.command == 'stage': stage(Path(args.zip).resolve(), Path(args.shared_dir).resolve())
        else: return receive(Path(args.package).resolve(), Path(args.zip).resolve(), Path(args.out).resolve())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print('ERROR: ' + str(exc)); return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
