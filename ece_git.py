"""Git transport. School run/push support Python 3.6; local commands use 3.10+."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
CATALOG = 'ece-workflow-catalog.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo, args, data=None, env=None):
    result = subprocess.run(['git'] + args, cwd=str(repo), input=data,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if result.returncode:
        raise ValueError('Git ' + args[0] + ' failed (code ' + str(result.returncode) + '); check network/authentication')
    return result.stdout


def safe_name(name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,240}', name):
        raise ValueError('Invalid transport filename')
    return name


def copy_exact(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if sha(source) != sha(dest): raise ValueError('Existing file differs: ' + dest.name)
        return
    temp = dest.with_name(dest.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_bytes(source.read_bytes())
    if sha(temp) != sha(source): raise ValueError('Copy hash mismatch')
    temp.replace(dest)


def export_packages(state, destination):
    from ece_workflow import registry
    rows = []
    for entry in registry(state)['packages']:
        name = safe_name(entry['archive'])
        source = Path(entry['package_dir']).with_suffix('.zip')
        if sha(source) != entry['archive_sha256']: raise ValueError('Source package changed')
        copy_exact(source, destination / name)
        rows.append({k: entry[k] for k in ('package_id', 'archive', 'archive_sha256', 'backend', 'label', 'cases')})
    if not rows: raise ValueError('No registered packages to export')
    save(destination / CATALOG, dict(schema=1, packages=rows,
         policy='Manually select ONE case per invocation; no EDA batch.'))
    print('Prepared for Git: ' + str(len(rows)) + ' unchanged packages in ' + str(destination))


def restore_packages(repo, state):
    import ece_station
    import ece_workflow as workflow
    source = repo / 'ece_git_packages'
    entries = read(source / CATALOG)['packages']
    reg = workflow.registry(state)
    for entry in entries:
        safe_name(entry['archive'])
        existing = [p for p in reg['packages'] if p['package_id'] == entry['package_id']]
        if existing:
            if len(existing) != 1 or existing[0]['archive_sha256'] != entry['archive_sha256']:
                raise ValueError('Package ID conflict')
            if Path(existing[0]['package_dir']).is_dir(): continue
        package_dir, package = ece_station.unpack(source, entry, state / 'restored')
        cases = [{k: m[k] for k in ('job_id', 'task', 'original_status', 'hashes')} for m in package['cases']]
        if cases != entry['cases']: raise ValueError('Catalog cases do not match frozen package')
        row = dict(entry, package_dir=str(package_dir), shared_dir=str(source),
                   run_dir='git-package:' + entry['label'])
        if existing: reg['packages'].remove(existing[0])
        reg['packages'].append(row)
    workflow.saved(state / 'registry.json', reg)


def make_commit(repo, files):
    """Use a temporary index: preserve caller HEAD, branch and staged changes."""
    with tempfile.TemporaryDirectory(prefix='ece-git-index-') as folder:
        env = os.environ.copy()
        env['GIT_INDEX_FILE'] = str(Path(folder) / 'index')
        env.update(GIT_AUTHOR_NAME='XZY01 ECE Runner', GIT_AUTHOR_EMAIL='ece-runner@localhost',
                   GIT_COMMITTER_NAME='XZY01 ECE Runner', GIT_COMMITTER_EMAIL='ece-runner@localhost')
        parent = git(repo, ['rev-parse', 'HEAD']).decode().strip()
        git(repo, ['read-tree', 'HEAD'], env=env)
        for name, content in files.items():
            if not re.fullmatch(r'ece_git_results/[a-f0-9]{32}/return-[A-Za-z0-9_.-]+\.(zip|json)', name):
                raise ValueError('Invalid Git result path')
            blob = git(repo, ['hash-object', '-w', '--stdin'], data=content).decode().strip()
            git(repo, ['update-index', '--add', '--cacheinfo', '100644', blob, name], env=env)
        tree = git(repo, ['write-tree'], env=env).decode().strip()
        return git(repo, ['commit-tree', tree, '-p', parent],
                   data=b'Preserve one ECE simulation attempt [skip ci]\n', env=env).decode().strip()


def upload(repo, state, remote='origin'):
    """Upload collected evidence only; safe to retry, never runs EDA."""
    ledger_path = state / 'uploads.json'
    ledger = read(ledger_path) if ledger_path.exists() else []
    state.mkdir(parents=True, exist_ok=True)
    lock = state / 'upload.lock'
    with lock.open('x') as stream:
        stream.write(str(os.getpid()))
    try:
        for sidecar in sorted((state / 'outbox').glob('return-*.json')):
            info = read(sidecar)
            archive = sidecar.parent / safe_name(info['archive'])
            if sha(archive) != info['archive_sha256'] or archive.stat().st_size > 100 * 1024 ** 2:
                raise ValueError('Invalid return archive')
            fingerprint = sha(sidecar) + ':' + info['archive_sha256']
            matches = [r for r in ledger if r['fingerprint'] == fingerprint]
            if matches: row = matches[0]
            else:
                key = uuid.uuid4().hex
                files = {'ece_git_results/' + key + '/' + p.name: p.read_bytes() for p in (sidecar, archive)}
                commit = make_commit(repo, files)
                row = dict(fingerprint=fingerprint, commit=commit, branch='ece-results/' + key, sent=False)
                # Keep a ref so GC cannot discard an unpushed result commit.
                git(repo, ['update-ref', 'refs/heads/' + row['branch'], commit])
                ledger.append(row)
                save(ledger_path, ledger)
            if row['sent']: continue
            # Inherit terminal input for Git's credential prompt. Never store a token.
            result = subprocess.call(['git', 'push', remote, row['commit'] + ':refs/heads/' + row['branch']], cwd=str(repo))
            if result:
                print('Result saved locally. Retry upload only: bash ece_git.sh push')
                return 2
            row['sent'] = True
            save(ledger_path, ledger)
        return 0
    finally:
        lock.unlink()


def blob(repo, ref, name, limit):
    size = int(git(repo, ['cat-file', '-s', ref + ':' + name]))
    if size > limit: raise ValueError('Git return file exceeds limit')
    return git(repo, ['show', ref + ':' + name])


def sync(repo, state, remote='origin'):
    import ece_workflow as workflow
    restore_packages(repo, state)
    # Restrict fetching to result branches; never merge or checkout returned code.
    if subprocess.call(['git', 'fetch', remote,
            'refs/heads/ece-results/*:refs/remotes/' + remote + '/ece-results/*'], cwd=str(repo)):
        raise ValueError('Could not fetch result branches')
    refs = git(repo, ['for-each-ref', '--format=%(refname)', 'refs/remotes/' + remote + '/ece-results/']).decode().splitlines()
    inbox = state / 'git-inbox' / 'inbox'
    inbox.mkdir(parents=True, exist_ok=True)
    issues = []
    for ref in refs:
        names = git(repo, ['ls-tree', '-r', '--name-only', ref, '--', 'ece_git_results']).decode().splitlines()
        for name in names:
            if not name.endswith('.json'): continue
            try:
                if not re.fullmatch(r'ece_git_results/[a-f0-9]{32}/return-[A-Za-z0-9_.-]+\.json', name):
                    raise ValueError('Unexpected metadata path')
                data = blob(repo, ref, name, 256 * 1024)
                info = json.loads(data.decode('utf-8'))
                archive_name = safe_name(info['archive'])
                if not archive_name.startswith('return-') or not archive_name.endswith('.zip'):
                    raise ValueError('Invalid archive filename')
                zip_path = str(PurePosixPath(name).parent / archive_name)
                raw = blob(repo, ref, zip_path, 100 * 1024 ** 2)
                if hashlib.sha256(raw).hexdigest() != info['archive_sha256']:
                    raise ValueError('Return ZIP hash mismatch')
                for filename, payload in ((archive_name, raw), (PurePosixPath(name).name, data)):
                    target = inbox / filename
                    if target.exists():
                        if target.read_bytes() != payload: raise ValueError('Conflicting return filename')
                    else:
                        with target.open('xb') as stream: stream.write(payload)
            except (OSError, ValueError, KeyError) as exc:
                issues.append(dict(ref=ref, file=name, error=str(exc)))
    save(state / 'git-sync-issues.json', issues)
    code = workflow.ingest(inbox.parent, state)
    print('Git transport issues: ' + str(len(issues)))
    return 1 if issues or code else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', nargs='?', choices=['run', 'push', 'export', 'sync'], default='run')
    p.add_argument('--state-dir', default=str(ROOT / 'workflow'))
    p.add_argument('--package-id')
    p.add_argument('--case')
    args = p.parse_args()
    state = ROOT / '.ece-git-state'
    try:
        if args.command == 'export':
            export_packages(Path(args.state_dir).resolve(), ROOT / 'ece_git_packages')
            return 0
        if args.command == 'sync': return sync(ROOT, Path(args.state_dir).resolve())
        origin = git(ROOT, ['config', '--get', 'remote.origin.url']).decode().strip()
        if origin not in ('https://github.com/Maxnopnop/xzy01-rtl-lab', 'https://github.com/Maxnopnop/xzy01-rtl-lab.git'):
            raise ValueError('School Git transport requires this project HTTPS origin')
        if args.command == 'push': return upload(ROOT, state)
        command = [sys.executable, str(ROOT / 'ece_station.py'), '--shared-dir', str(ROOT / 'ece_git_packages'),
                   '--return-dir', str(state / 'outbox')]
        if args.package_id: command += ['--package-id', args.package_id]
        if args.case: command += ['--case', args.case]
        code = subprocess.call(command)
        transport = upload(ROOT, state)
        return transport or code
    except (OSError, ValueError, KeyError) as exc:
        print('ERROR: ' + str(exc))
        return 2


if __name__ == '__main__':
    sys.exit(main())
