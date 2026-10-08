"""Python 3.6+ Linux station: choose a package and ONE case; auto-return evidence."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile


def choose(rows, label, read=input):
    if not rows: raise ValueError('No ' + label + ' available')
    for number, row in enumerate(rows, 1):
        print(str(number) + '. ' + row)
    answer = read('Choose ONE ' + label + ' number (0 exits): ').strip()
    if answer == '0': return None
    if not answer.isdigit() or not 1 <= int(answer) <= len(rows):
        raise ValueError('Invalid selection; no simulation started')
    return int(answer) - 1


def unpack(shared, entry, work):
    name = entry['archive']
    if Path(name).name != name: raise ValueError('Invalid package filename')
    archive = shared / name
    if hashlib.sha256(archive.read_bytes()).hexdigest() != entry['archive_sha256']:
        raise ValueError('Package ZIP hash mismatch')
    work.mkdir(parents=True, exist_ok=True)
    target = Path(tempfile.mkdtemp(prefix='session_', dir=str(work)))
    local = target / name; shutil.copyfile(str(archive), str(local))
    with zipfile.ZipFile(str(local)) as z:
        members = z.infolist(); seen = set()
        if len(members) > 5000 or sum(m.file_size for m in members) > 100 * 1024 * 1024:
            raise ValueError('Package exceeds limits')
        for m in members:
            parts = PurePosixPath(m.filename).parts
            if not parts or parts[0] != archive.stem or '..' in parts or '\\' in m.filename or ':' in m.filename or m.filename in seen or stat.S_ISLNK(m.external_attr >> 16):
                raise ValueError('Invalid ZIP path')
            seen.add(m.filename)
        z.extractall(str(target))
    root = target / archive.stem
    lock = json.loads((root / 'transfer-lock.json').read_text(encoding='utf-8'))
    for path, expected in lock.items():
        parts = PurePosixPath(path).parts
        if not parts or parts[0] == '/' or '..' in parts or '\\' in path or ':' in path:
            raise ValueError('Invalid lock path')
        source = root / path
        if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise ValueError('Package contents changed: ' + path)
    (root / 'station-provenance.json').write_text(json.dumps(dict(package_id=entry['package_id'],
        archive_sha256=entry['archive_sha256']), indent=2), encoding='utf-8')
    package = json.loads((root / 'package.json').read_text(encoding='utf-8'))
    if package['backend'] != entry['backend']: raise ValueError('Backend mismatch')
    return root, package


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--shared-dir', default=str(Path(__file__).resolve().parent))
    p.add_argument('--work-dir', default=str(Path.home() / 'xzy01-ece'))
    args = p.parse_args(); shared = Path(args.shared_dir).resolve()
    try:
        entries = json.loads((shared / 'ece-workflow-catalog.json').read_text(encoding='utf-8'))['packages']
        print('ECE station: manual ONE case per invocation; no SSH or EDA batch.')
        index = choose([e['label'] + ' | ' + e['backend'] + ' | ' + str(len(e['cases'])) + ' cases' for e in entries], 'package')
        if index is None: return 0
        root, package = unpack(shared, entries[index], Path(args.work_dir).resolve())
        print('School working directory: ' + str(root))
        result = subprocess.call([sys.executable, str(root / 'ece_desktop.py'), 'doctor'])
        if result: return result
        index = choose([m['job_id'] + ' | ' + m['task'] + ' | local=' + m['original_status'] for m in package['cases']], 'case')
        if index is None: return 0
        case = package['cases'][index]['job_id']
        print('Selected: ' + package['backend'] + ' / ' + case)
        return subprocess.call([sys.executable, str(root / 'ece_desktop.py'), 'session', '--case', case,
                                '--return-dir', str(shared / 'inbox')])
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as exc:
        print('ERROR: ' + str(exc)); return 2
    except (KeyboardInterrupt, EOFError):
        print('Selection cancelled'); return 130


if __name__ == '__main__': raise SystemExit(main())
