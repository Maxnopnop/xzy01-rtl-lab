"""CSV-configured API workbench; Python 3.10+, no external dependencies."""
import argparse
import csv
import getpass
import html
import io
import os
from pathlib import Path
import re
import subprocess
import sys

import batch
import rtl_lab as lab

ROOT = Path(__file__).resolve().parent
FIELDS = ['id', 'enabled', 'protocol', 'base_url', 'model', 'api_key_env']


def profiles(path, selected=None):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError('CSV columns must be: ' + ','.join(FIELDS) + '; store keys only in environment variables')
        rows = list(reader)
    ids = set()
    active = []
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError('Malformed CSV row')
        row = {k: v.strip() for k, v in row.items()}
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', row['id']) or row['id'].lower() in ids:
            raise ValueError('Profile IDs must be unique safe directory names')
        ids.add(row['id'].lower())
        if row['enabled'] not in ('true', 'false'):
            raise ValueError('enabled must be true or false')
        if row['enabled'] == 'false':
            continue
        if row['protocol'] != 'chat_completions':
            raise ValueError('Only chat_completions is supported; native provider protocols need adapters')
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', row['api_key_env']):
            raise ValueError('Invalid environment variable name')
        if not row['model']:
            raise ValueError('Set an explicit model ID')
        # Local syntax validation only; never make a request here.
        lab.validate_endpoint(row['base_url'], True, '')
        if row['base_url'].rstrip('/').endswith('/chat/completions'):
            raise ValueError('Use the base URL, not the full /chat/completions endpoint')
        active.append(row)
    if selected:
        wanted = selected.split(',')
        if len(set(wanted)) != len(wanted) or set(wanted) - {r['id'] for r in active}:
            raise ValueError('Unknown, disabled or duplicate selected model ID')
        active = [r for r in active if r['id'] in wanted]
    if not active:
        raise ValueError('Enable at least one profile in CSV')
    return active


def selection(suite, tasks, samples):
    specs = batch.manifest(suite)
    wanted = [s['id'] for s in specs] if tasks == 'all' else tasks.split(',')
    if not wanted or len(set(wanted)) != len(wanted) or set(wanted) - {s['id'] for s in specs}:
        raise ValueError('Unknown or duplicate task ID')
    if samples < 1 or len(wanted) * samples > 10000:
        raise ValueError('Invalid sample count')
    return len(wanted) * samples


def keys(rows, prompt=False):
    for name in dict.fromkeys(r['api_key_env'] for r in rows):
        if not os.environ.get(name) and prompt:
            value = getpass.getpass(name + ' (hidden, process memory only): ')
            if value:
                os.environ[name] = value
        if not os.environ.get(name):
            raise ValueError('Missing environment variable: ' + name + '; use --prompt-keys or set it locally')


def invoke(argv):
    return subprocess.run([sys.executable, str(ROOT / 'batch.py')] + argv, cwd=ROOT, check=False).returncode


def prepare(args, rows):
    count = selection(args.suite, args.tasks, args.samples)
    if args.max_total_calls < len(rows) * count:
        raise ValueError('Planned calls exceed --max-total-calls; reduce profiles/tasks/samples')
    keys(rows, args.prompt_keys)
    root = Path(args.run_dir).resolve()
    if root.exists():
        raise ValueError('Use a new run directory; resume with run')
    root.mkdir(parents=True)
    entries = []
    for row in rows:
        target = root / row['id']
        argv = ['init', '--run-dir', str(target), '--mode', 'live', '--suite', args.suite,
                '--tasks', args.tasks, '--samples', str(args.samples), '--max-calls', str(count),
                '--base-url', row['base_url'], '--model', row['model'], '--api-key-env', row['api_key_env'],
                '--max-output-tokens', str(args.max_output_tokens), '--api-timeout', str(args.api_timeout),
                '--token-field', args.token_field]
        for name in ('temperature', 'iverilog', 'vvp'):
            value = getattr(args, name)
            if value is not None:
                argv += ['--' + name, str(value)]
        if invoke(argv):
            raise ValueError('Preparation failed; no API calls made. Use a new run directory after fixing configuration')
        entries.append(dict(profile=row, directory=row['id'], max_calls=count,
                            plan_sha256=lab.digest((target / 'plan.json').read_bytes())))
    batch.atomic(root / 'platform.json', dict(schema=1, profiles=entries,
        max_total_calls=args.max_total_calls, planned_calls=len(rows) * count,
        workbench_sha256=lab.digest(Path(__file__).read_bytes()),
        note='Direct RTL baseline only; adapted development subset. No automatic retries or cross-model fallback.'))
    report(root)
    print('Prepared with zero API calls: ' + str(root))


def load(root):
    plan = batch.read(root / 'platform.json')
    if plan['workbench_sha256'] != lab.digest(Path(__file__).read_bytes()):
        raise ValueError('Workbench changed; create a new experiment')
    for item in plan['profiles']:
        name = item['directory']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', name):
            raise ValueError('Unsafe profile directory')
        folder = root / name
        if lab.digest((folder / 'plan.json').read_bytes()) != item['plan_sha256']:
            raise ValueError('Frozen model plan changed')
    return plan


def report(root):
    plan = load(root)
    rows = []
    for item in plan['profiles']:
        result = batch.report(root / item['directory'])
        rows.append(dict(id=item['directory'], model=item['profile']['model'],
            planned=result['planned'], completed=result['completed'], pending=result['pending'],
            passes=result['counts'].get('PASS', 0), calls=result['model_call_reservations'],
            counts=result['counts'], usage=result['recorded_token_usage']))
    batch.atomic(root / 'platform-summary.json', dict(profiles=rows, planned_calls=plan['planned_calls'],
        reserved_calls=sum(r['calls'] for r in rows), max_total_calls=plan['max_total_calls']))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    (root / 'platform-summary.csv').write_text(stream.getvalue(), encoding='utf-8-sig')
    body = ''.join('<tr>' + ''.join('<td>' + html.escape(str(r[k])) + '</td>'
        for k in ('id', 'model', 'planned', 'completed', 'pending', 'passes', 'calls')) + '</tr>' for r in rows)
    (root / 'platform-report.html').write_text('<!doctype html><meta charset="utf-8"><title>API 模型实验</title>'
        '<h1>API 模型实验</h1><p>开发集直接生成 RTL；未完成和失败保留在分母内。</p>'
        '<table border="1"><tr><th>ID</th><th>模型</th><th>计划</th><th>完成</th><th>待执行</th>'
        '<th>通过</th><th>调用预留</th></tr>' + body + '</table>', encoding='utf-8')
    return rows


def run(args):
    root = Path(args.run_dir).resolve()
    if (root / 'exact-prompts.json').exists():
        raise ValueError('This run uses verbatim prompts; continue with lab.ps1 local --prompt-dir, not the default prompt runner')
    plan = load(root)
    keys([i['profile'] for i in plan['profiles']], args.prompt_keys)
    with batch.lock(root):
        for item in plan['profiles']:
            folder = root / item['directory']
            bp = batch.read(folder / 'plan.json')
            # Frozen batch resumes interrupted slots automatically. At this layer an
            # unknown outcome requires review, so block instead of issuing another call.
            saved = [batch.latest(folder, j) for j in bp['jobs']]
            if any(r and r['status'] == 'INTERRUPTED' for r in saved):
                raise ValueError('Interrupted outcome retained; review it and create a separate run for any retry')
            if any((folder / 'jobs' / j['id']).exists() and r is None for j, r in zip(bp['jobs'], saved)):
                raise ValueError('Unfinished attempt has an unknown outcome; review before a separate retry run')
            used = sum(r['calls'] for r in report(root))
            remaining = sum(r is None for r in saved)
            if used + remaining > plan['max_total_calls']:
                raise ValueError('Global reservation budget exhausted; no further requests')
            code = invoke(['run', '--run-dir', str(folder), '--workers', str(args.workers)])
            report(root)
            if code not in (0, 1):
                raise ValueError('Model runner failed; evidence saved')
            current = [batch.latest(folder, j) for j in bp['jobs']]
            if any(r and r['status'] in ('API_ERROR', 'ENV_ERROR', 'INTERRUPTED') for r in current):
                raise ValueError('Infrastructure failure retained; review before continuing other profiles')
    rows = report(root)
    return 0 if all(r['passes'] == r['planned'] for r in rows) else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    template = sub.add_parser('template')
    template.add_argument('--output', default='config.local.models.csv')
    for command in ('check', 'prepare'):
        p = sub.add_parser(command)
        p.add_argument('--profiles', default='config.local.models.csv')
        p.add_argument('--models', help='Comma-separated enabled profile IDs')
        p.add_argument('--suite', choices=batch.SUITES, default='dev10')
        p.add_argument('--tasks', default='all')
        p.add_argument('--samples', type=int, default=1)
        if command == 'prepare':
            p.add_argument('--run-dir', required=True)
            p.add_argument('--max-total-calls', type=int, required=True)
            p.add_argument('--prompt-keys', action='store_true')
            p.add_argument('--max-output-tokens', type=int, default=4096)
            p.add_argument('--api-timeout', type=lab.positive, default=180)
            p.add_argument('--temperature', type=float)
            p.add_argument('--token-field', choices=['max_tokens', 'max_completion_tokens'], default='max_tokens')
            p.add_argument('--iverilog', default=os.environ.get('IVERILOG'))
            p.add_argument('--vvp', default=os.environ.get('VVP'))
    for command in ('run', 'report'):
        p = sub.add_parser(command)
        p.add_argument('--run-dir', required=True)
        if command == 'run':
            p.add_argument('--workers', type=int, choices=range(1, 17), default=1)
            p.add_argument('--prompt-keys', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'template':
            with Path(args.output).open('x', encoding='utf-8-sig', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                for name in ('vendor_a', 'vendor_b'):
                    writer.writerow(dict(id=name, enabled='false', protocol='chat_completions',
                        base_url='https://api.example.com/v1', model='REPLACE_MODEL_ID', api_key_env=name.upper() + '_API_KEY'))
            print('Created: ' + args.output)
        elif args.command in ('check', 'prepare'):
            rows = profiles(args.profiles, args.models)
            count = selection(args.suite, args.tasks, args.samples)
            if args.command == 'check':
                for row in rows:
                    print(row['id'] + ': ' + row['model'] + '; key=' + ('SET' if os.environ.get(row['api_key_env']) else 'MISSING'))
                print('Planned calls: ' + str(count * len(rows)) + '; no network request made')
            else:
                prepare(args, rows)
        elif args.command == 'run':
            return run(args)
        else:
            report(Path(args.run_dir).resolve())
    except (ValueError, OSError, KeyError, lab.LabError, EOFError) as exc:
        # Never echo user-supplied file contents, endpoints or credential values.
        print('ERROR: ' + (str(exc) if isinstance(exc, (ValueError, lab.LabError)) else type(exc).__name__), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
