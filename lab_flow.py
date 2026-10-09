"""Unified local FYP workflow: API -> Icarus -> Yosys -> ECE transport/report."""
import argparse
import csv
import html
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import batch
import ece_desktop as desktop
import ece_git
import ece_workflow as workflow
import model_platform
import exact_prompts

ROOT = Path(__file__).resolve().parent


def command(args, capture=False):
    result = subprocess.run(args, cwd=ROOT, check=False,
        stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None)
    if result.returncode not in (0, 1):
        raise ValueError('Command failed: ' + Path(args[0]).name)
    return result


def synthesis_mode(mode, distro):
    if mode == 'none': return 'none'
    if mode in ('auto', 'native') and shutil.which('yosys'): return 'native'
    if mode in ('auto', 'wsl') and os.name == 'nt' and shutil.which('wsl'):
        result = command(['wsl', '-d', distro, '--', 'python3', '-c',
                          'import shutil,sys;sys.exit(0 if shutil.which("yosys") else 1)'], True)
        if result.returncode == 0: return 'wsl'
    raise ValueError('Yosys unavailable; install/configure it or explicitly choose --synthesis none')


def synthesize(run, mode, distro='Ubuntu'):
    if mode == 'none': return
    if mode == 'native':
        result = command([sys.executable, str(ROOT / 'synthesis.py'), '--run-dir', str(run)])
    else:
        def linux(path):
            p = command(['wsl', '-d', distro, '--', 'wslpath', '-u', str(path)], True)
            if p.returncode: raise ValueError('WSL path conversion failed')
            return p.stdout.decode('utf-8').strip()
        result = command(['wsl', '-d', distro, '--', 'python3', linux(ROOT / 'synthesis.py'), '--run-dir', linux(run)])
    if not (run / 'synthesis-review' / 'summary.json').is_file():
        raise ValueError('Synthesis did not produce a summary')
    return result.returncode


def runs_under(root):
    if (root / 'platform.json').is_file():
        plan = model_platform.load(root)
        return [root / p['directory'] for p in plan['profiles']]
    if (root / 'plan.json').is_file(): return [root]
    raise ValueError('Expected a model platform directory or an existing run directory')


def stage(run, backends, shared, state):
    bp = batch.read(run / 'plan.json')
    selected = [j['id'] for j in bp['jobs'] if (batch.latest(run, j) or {}).get('rtl_sha256')]
    if not selected:
        print('No accepted RTL available for export: ' + str(run))
        return
    for backend in backends.split(','):
        if backend not in ('vcs', 'xcelium'): raise ValueError('Expected vcs,xcelium')
        matches = [p for p in workflow.registry(state)['packages'] if
            p['run_dir'] == str(run) and p['backend'] == backend and
            [m['job_id'] for m in p['cases']] == selected and Path(p['shared_dir']).resolve() == shared]
        if matches:
            original = matches[-1]
            package_dir = Path(original['package_dir'])
            desktop.verify(package_dir)
            for m in original['cases']:
                current = batch.latest(run, next(j for j in bp['jobs'] if j['id'] == m['job_id']))
                if current['rtl_sha256'] != m['hashes']['dut.sv']:
                    raise ValueError('Previously staged source changed; use a new run')
            ece_git.copy_exact(package_dir.with_suffix('.zip'), shared / original['archive'])
            workflow.publish(shared, workflow.registry(state))
            print('Existing package reused: ' + original['package_id'])
        else:
            workflow.prepare(run, ','.join(selected), backend, shared, state)


def report(state, root=None):
    school = workflow.status(state)
    rows = []
    runs = runs_under(root) if root else [ROOT / e['run'] for e in workflow.history()]
    for run in runs:
        bp = batch.read(run / 'plan.json')
        for job in bp['jobs']:
            row = batch.latest(run, job) or {}
            review = run / 'synthesis-review' / job['id'] / 'result.json'
            synth = row.get('synthesis_status', 'NOT_RUN')
            if review.is_file():
                data = batch.read(review)
                result_path = run / 'jobs' / job['id'] / 'result.json'
                if data.get('rtl_sha256') != row.get('rtl_sha256') or not result_path.exists() or data.get('source_result_sha256') != desktop.digest(result_path):
                    raise ValueError('Synthesis result does not bind current RTL/result')
                synth = data['status']
            item = dict(run=str(run), job=job['id'], model=bp['config'].get('model', ''),
                        icarus=row.get('status', 'PENDING'), yosys=synth)
            for backend in ('vcs', 'xcelium'):
                matches = [r for r in school['rows'] if r['experiment'] == str(run) and r['job_id'] == job['id'] and r['backend'] == backend]
                done = [r for r in matches if r['attempts']]
                item[backend] = done[-1]['commercial'] if done else 'NOT_RUN'
            rows.append(item)
    workflow.saved(state / 'lab-summary.json', dict(rows=rows, note='Development results; no PPA/formal-equivalence claim.'))
    fields = ['run', 'job', 'model', 'icarus', 'yosys', 'vcs', 'xcelium']
    with (state / 'lab-summary.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    body = ''.join('<tr>' + ''.join('<td>' + html.escape(str(row[k])) + '</td>' for k in fields) + '</tr>' for row in rows)
    (state / 'lab-report.html').write_text('<!doctype html><meta charset="utf-8"><title>FYP workflow</title>'
        '<style>body{font:15px system-ui;padding:24px}td,th{padding:8px;border:1px solid #ccc}table{border-collapse:collapse}</style>'
        '<h1>FYP 工具链结果</h1><p>NOT_RUN 表示尚未验证。商业工具每次只运行一个人工选择的案例。</p>'
        '<p><a href="report.html">学校所有包与尝试</a> · <a href="lab-summary.csv">下载 CSV</a></p>'
        '<table><tr>' + ''.join('<th>' + k + '</th>' for k in fields) + '</tr>' + body + '</table>', encoding='utf-8')
    print('Unified report: ' + str(state / 'lab-report.html'))
    return rows


def publish_git(state, push):
    ece_git.export_packages(state, ROOT / 'ece_git_packages')
    if not push: return
    branch = ece_git.git(ROOT, ['rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
    if branch != 'main': raise ValueError('Package publication requires main; commit code separately first')
    ece_git.git(ROOT, ['add', '--', 'ece_git_packages'])
    changed = subprocess.call(['git', 'diff', '--cached', '--quiet', '--', 'ece_git_packages'], cwd=ROOT)
    if changed == 1:
        ece_git.git(ROOT, ['commit', '--only', '-m', 'Publish frozen ECE simulation packages', '--', 'ece_git_packages'])
    elif changed != 0: raise ValueError('Could not check staged package changes')
    if subprocess.call(['git', 'push', 'origin', 'HEAD:main'], cwd=ROOT):
        raise ValueError('Package push failed; local commit preserved')


def local(args):
    root = Path(args.run_dir).resolve()
    mode = synthesis_mode(args.synthesis, args.wsl_distro)
    if args.prompt_dir and args.workers != 1:
        raise ValueError('Verbatim prompt mode currently requires --workers 1')
    if args.prompt_dir:
        selected = [s['id'] for s in batch.manifest(args.suite)] if args.tasks == 'all' else args.tasks.split(',')
        for task in selected:
            data = (Path(args.prompt_dir) / (task + '.txt')).read_bytes()
            data.decode('utf-8')
            if not data or len(data) > 1024 * 1024: raise ValueError('Full prompt must be nonempty UTF-8 and at most 1 MiB')
    if not root.exists():
        init = ['prepare', '--profiles', args.profiles, '--run-dir', str(root), '--suite', args.suite,
                '--tasks', args.tasks, '--samples', str(args.samples), '--max-total-calls', str(args.max_total_calls)]
        if args.prompt_keys: init += ['--prompt-keys']
        for name in ('models', 'iverilog', 'vvp'):
            value = getattr(args, name)
            if value: init += ['--' + name, value]
        if model_platform.main(init): return 2
        if args.prompt_dir: exact_prompts.freeze(root, Path(args.prompt_dir))
    else:
        # Do not allow a changed CSV to silently change the meaning of a resume.
        frozen = model_platform.load(root)
        profiles = model_platform.profiles(args.profiles, args.models)
        if profiles != [p['profile'] for p in frozen['profiles']]:
            raise ValueError('Profiles differ from this frozen run; restore CSV or use a new run directory')
        for p in frozen['profiles']:
            bp = batch.read(root / p['directory'] / 'plan.json')
            count = model_platform.selection(args.suite, args.tasks, args.samples)
            tasks = [s['id'] for s in batch.manifest(args.suite)] if args.tasks == 'all' else args.tasks.split(',')
            if bp['config']['suite'] != args.suite or set(tasks) != {j['task'] for j in bp['jobs']} or len(bp['jobs']) != count or frozen['max_total_calls'] != args.max_total_calls:
                raise ValueError('Resume settings differ; reuse original options or start a new run')
        if bool(args.prompt_dir) != (root / 'exact-prompts.json').exists():
            raise ValueError('Cannot switch prompt modes on resume')
        if args.prompt_dir:
            cfg = exact_prompts.verify(root)
            for task, digest in cfg['hashes'].items():
                if desktop.digest(Path(args.prompt_dir) / (task + '.txt')) != digest:
                    raise ValueError('Original prompt changed; create a new run')
    run_args = ['run', '--run-dir', str(root), '--workers', str(args.workers)]
    if args.prompt_keys: run_args += ['--prompt-keys']
    code = exact_prompts.run(root, args.prompt_keys) if args.prompt_dir else model_platform.main(run_args)
    if code not in (0, 1):
        print('Local model stage incomplete; evidence preserved. No further stages started.')
        return code
    for run in runs_under(root):
        if any(batch.latest(run, j) is None for j in batch.read(run / 'plan.json')['jobs']):
            raise ValueError('Generation has pending slots; complete/review before synthesis')
        synthesize(run, mode, args.wsl_distro)
        stage(run, args.backends, Path(args.shared_dir).resolve(), Path(args.state_dir).resolve())
    report(Path(args.state_dir).resolve(), root)
    if args.publish_git: publish_git(Path(args.state_dir).resolve(), True)
    print('Local workflow saved. Next: run ece_menu.sh in the school desktop and select ONE case.')
    return code


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state-dir', default=str(workflow.DEFAULT_STATE))
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    a = sub.add_parser('local')
    a.add_argument('--run-dir', required=True)
    a.add_argument('--profiles', default='config.local.models.csv')
    a.add_argument('--prompt-dir', help='Directory of exact UTF-8 prompts named <task_id>.txt; no added instructions')
    a.add_argument('--models')
    a.add_argument('--suite', choices=batch.SUITES, default='dev10')
    a.add_argument('--tasks', default='all')
    a.add_argument('--samples', type=int, default=1)
    a.add_argument('--max-total-calls', type=int, required=True)
    a.add_argument('--prompt-keys', action='store_true')
    a.add_argument('--workers', type=int, choices=range(1, 17), default=1)
    a.add_argument('--synthesis', choices=['auto', 'native', 'wsl', 'none'], default='auto')
    a.add_argument('--wsl-distro', default='Ubuntu')
    a.add_argument('--iverilog', default=os.environ.get('IVERILOG'))
    a.add_argument('--vvp', default=os.environ.get('VVP'))
    a.add_argument('--publish-git', action='store_true')
    a.add_argument('--backends', default='vcs,xcelium')
    a.add_argument('--shared-dir', default=str(workflow.DEFAULT_SHARED))
    a = sub.add_parser('prompt')
    a.add_argument('--task', default='full_prompt')
    a.add_argument('--dir', default='config.local.prompts')
    a.add_argument('--no-open', action='store_true')
    a = sub.add_parser('generate')
    a.add_argument('--prompt-file', required=True)
    a.add_argument('--run-dir', required=True)
    a.add_argument('--profiles', default='config.local.models.csv')
    a.add_argument('--models')
    a.add_argument('--samples', type=int, default=1)
    a.add_argument('--max-total-calls', type=int, required=True)
    a.add_argument('--prompt-keys', action='store_true')
    a.add_argument('--token-field', choices=['max_tokens', 'max_completion_tokens'], default='max_tokens')
    a.add_argument('--max-output-tokens', type=int, default=4096)
    a.add_argument('--api-timeout', type=batch.lab.positive, default=180)
    a = sub.add_parser('stage')
    a.add_argument('--run-dir', required=True)
    a.add_argument('--backends', default='vcs,xcelium')
    a.add_argument('--shared-dir', default=str(workflow.DEFAULT_SHARED))
    a = sub.add_parser('export-git')
    a.add_argument('--push', action='store_true')
    a = sub.add_parser('collect')
    a.add_argument('--shared-dir', default=str(workflow.DEFAULT_SHARED))
    a.add_argument('--git', action='store_true')
    a.add_argument('--run-dir')
    a = sub.add_parser('report')
    a.add_argument('--run-dir')
    a = sub.add_parser('backup')
    a.add_argument('--output', required=True)
    args = p.parse_args(argv)
    state = Path(args.state_dir).resolve()
    try:
        if args.command == 'doctor':
            tools = {name: shutil.which(name) for name in ('iverilog', 'vvp', 'yosys', 'wsl', 'git')}
            print(json.dumps(dict(python=sys.version.split()[0], tools=tools,
                shared_exists=workflow.DEFAULT_SHARED.is_dir(), repo=str(ROOT)), indent=2))
            print('No API/network/EDA request made. Windows Yosys may run via WSL Ubuntu.')
        elif args.command == 'local': return local(args)
        elif args.command == 'generate': return exact_prompts.generate_only(args)
        elif args.command == 'prompt':
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.task):
                raise ValueError('Use a simple task ID')
            folder = Path(args.dir).resolve()
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / (args.task + '.txt')
            if not target.exists(): target.write_bytes(b'')
            print('Paste the complete prompt here and save as UTF-8. No wrapper text will be added: ' + str(target))
            if os.name == 'nt' and not args.no_open: subprocess.Popen(['notepad.exe', str(target)])
        elif args.command == 'stage':
            for run in runs_under(Path(args.run_dir).resolve()):
                stage(run, args.backends, Path(args.shared_dir).resolve(), state)
            report(state, Path(args.run_dir).resolve())
        elif args.command == 'export-git': publish_git(state, args.push)
        elif args.command == 'collect':
            code = workflow.ingest(Path(args.shared_dir).resolve(), state)
            if args.git: code = ece_git.sync(ROOT, state) or code
            report(state, Path(args.run_dir).resolve() if args.run_dir else None)
            return code
        elif args.command == 'report': report(state, Path(args.run_dir).resolve() if args.run_dir else None)
        else:
            output = Path(args.output).resolve()
            if output.is_relative_to(state) or output.is_relative_to(ROOT / 'runs'):
                raise ValueError('Backup output must be outside workflow/ and runs/')
            output.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
                for base in (state, ROOT / 'runs'):
                    for path in base.rglob('*'):
                        if path.is_file() and not path.is_symlink():
                            archive.write(path, base.name + '/' + path.relative_to(base).as_posix())
            print('Local evidence backup (keep private): ' + str(output))
    except (ValueError, OSError, KeyError, batch.lab.LabError) as exc:
        print('ERROR: ' + str(exc))
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
