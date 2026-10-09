"""Opt-in verbatim user prompts. No system message, prefix, suffix or trimming."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import batch
import rtl_lab as lab
import model_platform as platform

ROOT = Path(__file__).resolve().parent


def freeze(root, source):
    plan = platform.load(root)
    tasks = batch.read(root / plan['profiles'][0]['directory'] / 'plan.json')['tasks']
    contents = {}
    for task in tasks:
        data = (source / (task['id'] + '.txt')).read_bytes()
        data.decode('utf-8')  # Reject unsupported encodings; do not convert or trim.
        if not data or len(data) > 1024 * 1024:
            raise ValueError('Each full prompt must contain 1..1048576 UTF-8 bytes')
        contents[task['id']] = data
    target = root / 'exact-prompts'
    target.mkdir()
    for task, data in contents.items():
        (target / (task + '.txt')).write_bytes(data)
    batch.atomic(root / 'exact-prompts.json', dict(schema=1,
        hashes={k: lab.digest(v) for k, v in contents.items()},
        worker_sha256=lab.digest(Path(__file__).read_bytes()),
        mode='One user message only; no system message or added text'))


def verify(root):
    cfg = batch.read(root / 'exact-prompts.json')
    if cfg['worker_sha256'] != lab.digest(Path(__file__).read_bytes()):
        raise ValueError('Exact-prompt worker changed; create a new experiment')
    for task, digest in cfg['hashes'].items():
        if lab.digest((root / 'exact-prompts' / (task + '.txt')).read_bytes()) != digest:
            raise ValueError('Frozen original prompt changed')
    return cfg


def payload(config, data):
    # Decode only; read_text/newline conversion and strip() are deliberately absent.
    text = data.decode('utf-8')
    if text.encode('utf-8') != data: raise ValueError('Prompt byte roundtrip failed')
    request = dict(model=config['model'], messages=[dict(role='user', content=text)], stream=False)
    request[config['token_field']] = config['max_output_tokens']
    for name in ('temperature', 'seed'):
        if config.get(name) is not None: request[name] = config[name]
    return request


def generate(args, folder, request, secret):
    """Keep request content exact; redact credentials only from response logs."""
    endpoint = lab.validate_endpoint(args.base_url, False, secret)
    path = folder / 'api_request.json'
    path.write_text(json.dumps(dict(endpoint=endpoint, payload=request), ensure_ascii=False), encoding='utf-8')
    if json.loads(path.read_text(encoding='utf-8'))['payload'] != request:
        raise ValueError('Saved request differs from original')
    env = lab.clean_env()
    env['RTL_LAB_API_SECRET'] = secret
    result = lab.run_process([sys.executable, str(ROOT / 'api_worker.py'), str(path), str(args.api_timeout)],
                             folder, args.api_timeout, env)
    lab.save_process(folder, 'api', result, secret)
    if result['timeout'] or result['output_limit']:
        raise lab.LabError('API_ERROR', 'api', 'Timeout/output limit; no automatic retry')
    try:
        envelope = json.loads(result['stdout'])
        if result['returncode'] or not envelope.get('ok'):
            raise lab.LabError('API_ERROR', 'api', envelope.get('error', 'Request failed'))
        lab.write_text(folder / 'api_response.raw.json', envelope['body'], secret)
        body = json.loads(envelope['body'])
        choices = body['choices']
        raw = choices[0]['message']['content']
        if len(choices) != 1 or not isinstance(raw, str) or not raw.strip(): raise ValueError()
    except (ValueError, KeyError, TypeError, IndexError):
        raise lab.LabError('API_ERROR', 'api', 'Expected one nonempty text completion') from None
    lab.write_text(folder / 'model_output.raw.txt', raw, secret)
    if choices[0].get('finish_reason') == 'length':
        raise lab.LabError('EXTRACTION_ERROR', 'extraction', 'Output truncated; response retained')
    return raw, dict(response_model=body.get('model'), response_id=body.get('id'), usage=body.get('usage'),
                     finish_reason=choices[0].get('finish_reason'), http_status=envelope.get('http_status'))


def worker(root, model_dir, job_id, attempt):
    cfg = verify(root)
    run = root / model_dir
    plan = batch.read(run / 'plan.json')
    if batch.identity(plan['config']['suite']) != plan['source_hashes']:
        raise ValueError('Frozen runtime changed')
    job = next(j for j in plan['jobs'] if j['id'] == job_id)
    spec = next(s for s in plan['tasks'] if s['id'] == job['task'])
    config = plan['config']
    args = SimpleNamespace(**config)
    secret = os.environ.get(config['api_key_env'], '')
    data = (root / 'exact-prompts' / (job['task'] + '.txt')).read_bytes()
    request = payload(config, data)
    row = dict(schema=2, job_id=job_id, task=job['task'], sample=job['sample'], mode='live',
        source_label='LIVE_API_EXACT_USER_PROMPT', requested_model=config['model'],
        prompt_sha256=cfg['hashes'][job['task']], attempt=attempt.name, directory=str(attempt.relative_to(run)),
        live_api_success=False, synthesis_status='NOT_REQUESTED', joint_pass=False)
    try:
        lab.validate_endpoint(args.base_url, False, secret)
        if secret and secret in data.decode('utf-8'):
            raise ValueError('Prompt contains the API credential; refuse rather than redact or modify the request')
        # Inspect tools before spending a call; initialize environment in the same
        # format the frozen runner uses for later synthesis/export.
        tools = lab.inspect_tools(args, attempt)
        environment = run / 'environment.json'
        if environment.exists() and batch.read(environment)['tools'] != tools:
            raise ValueError('Simulator changed; create a new experiment')
        if not environment.exists():
            batch.atomic(environment, dict(tools=tools, python=sys.version, mode='EXACT_USER_PROMPT'))
        lab.write_json(attempt / 'prompt.json', dict(mode='EXACT_USER_PROMPT', request=request), secret)
        (attempt / 'prompt-original.txt').write_bytes(data)
        raw, meta = generate(args, attempt, request, secret)
        row.update(meta, live_api_success=True)
        rtl = lab.extract_rtl(raw, spec['module'])
        fixture = attempt / 'generated'
        fixture.mkdir()
        (fixture / (spec['id'] + '.sv')).write_text(rtl, encoding='utf-8')
        offline = SimpleNamespace(**config)
        offline.mode = 'offline'
        offline.rtl_dir = str(fixture)
        offline.label = 'EXACT_PROMPT_RTL_EVALUATION'
        evaluated = lab.evaluate(offline, attempt, spec, 1, tools, secret)
        folder = attempt / evaluated['directory']
        # The offline evaluator's generic prompt is diagnostic context only;
        # rename it so it cannot be mistaken for a sent API request.
        (folder / 'prompt.json').rename(folder / 'offline-evaluator-context.json')
        evaluated['directory'] = folder.relative_to(run).as_posix()
        row.update(evaluated)
        row.update(meta, mode='live', source_label='LIVE_API_EXACT_USER_PROMPT', live_api_success=True,
            job_id=job_id, sample=job['sample'], attempt=attempt.name,
            prompt_sha256=cfg['hashes'][job['task']])
        lab.write_json(folder / 'result.json', row, secret)
    except lab.LabError as exc:
        row.update(status=exc.status, stage=exc.stage, message=exc.message)
    except (OSError, ValueError, KeyError) as exc:
        row.update(status='ENV_ERROR', stage='exact_worker', message=type(exc).__name__)
    row.setdefault('simulation_status', row.get('status', 'ENV_ERROR'))
    lab.write_json(attempt / 'result.json', row, secret)
    lab.write_json(run / 'jobs' / job_id / 'result.json', row, secret)
    return 0 if row['status'] == 'PASS' else 1


def run(root, prompt_keys=False):
    verify(root)
    plan = platform.load(root)
    platform.keys([p['profile'] for p in plan['profiles']], prompt_keys)
    with batch.lock(root):
        for profile in plan['profiles']:
            folder = root / profile['directory']
            bp = batch.read(folder / 'plan.json')
            with batch.lock(folder):
                for job in bp['jobs']:
                    prior = batch.latest(folder, job)
                    if prior:
                        if prior['status'] == 'INTERRUPTED': raise ValueError('Unknown interrupted outcome; no automatic retry')
                        continue
                    jobdir = folder / 'jobs' / job['id']
                    if jobdir.exists(): raise ValueError('Unknown previous attempt; no automatic retry')
                    summaries = platform.report(root)
                    reserved = sum(r['calls'] for r in summaries)
                    model_used = next(r['calls'] for r in summaries if r['id'] == profile['directory'])
                    if reserved >= plan['max_total_calls'] or model_used >= profile['max_calls']:
                        raise ValueError('Call reservation cap reached')
                    attempt = jobdir / 'attempt_001'
                    attempt.mkdir(parents=True)
                    batch.atomic(attempt / 'started.json', dict(model_call_reserved=True, started_utc=lab.utc()))
                    try:
                        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), '_worker',
                            '--run-dir', str(root), '--model-dir', profile['directory'], '--job-id', job['id'],
                            '--attempt', str(attempt)], check=False)
                    except KeyboardInterrupt:
                        # Worker state remains evidence of an unknown outcome.
                        raise ValueError('Interrupted; attempt preserved, do not automatically retry')
                    result = batch.latest(folder, job)
                    if proc.returncode not in (0, 1) or result is None:
                        raise ValueError('Worker incomplete; inspect attempt, no automatic retry')
                    platform.report(root)
                    if result['status'] in ('API_ERROR', 'ENV_ERROR', 'INTERRUPTED'):
                        raise ValueError('Infrastructure failure retained; no automatic retries')
    rows = platform.report(root)
    return 0 if all(r['passes'] == r['planned'] for r in rows) else 1


def generate_only(args):
    """Arbitrary full prompt without claiming a testbench or functional score."""
    root = Path(args.run_dir).resolve()
    if root.exists(): raise ValueError('Use a new directory; unverified generation does not automatically retry')
    data = Path(args.prompt_file).read_bytes()
    text = data.decode('utf-8')
    if not data or len(data) > 1024 * 1024: raise ValueError('Prompt must be 1..1048576 UTF-8 bytes')
    profiles = platform.profiles(args.profiles, args.models)
    if args.samples < 1 or args.max_output_tokens < 1 or len(profiles) * args.samples > args.max_total_calls:
        raise ValueError('Planned calls exceed the explicit budget')
    platform.keys(profiles, args.prompt_keys)
    if any(os.environ[p['api_key_env']] in text for p in profiles):
        raise ValueError('Prompt contains an API credential; no request sent')
    root.mkdir(parents=True)
    (root / 'prompt-original.txt').write_bytes(data)
    lab.write_json(root / 'generation-plan.json', dict(profiles=profiles, samples=args.samples,
        prompt_sha256=lab.digest(data), max_total_calls=args.max_total_calls, validation='NONE'))
    rows = []
    for p in profiles:
        config = dict(p, allow_anonymous=False, api_timeout=args.api_timeout, token_field=args.token_field, max_output_tokens=args.max_output_tokens)
        for sample in range(1, args.samples + 1):
            folder = root / p['id'] / ('sample_' + str(sample))
            folder.mkdir(parents=True)
            lab.write_json(folder / 'started.json', dict(model_call_reserved=True, started_utc=lab.utc()))
            row = dict(profile=p['id'], sample=sample, status='STARTED', prompt_sha256=lab.digest(data))
            try:
                _, meta = generate(SimpleNamespace(**config), folder, payload(config, data), os.environ[p['api_key_env']])
                row.update(meta, status='GENERATED_UNVERIFIED')
            except lab.LabError as exc:
                row.update(status=exc.status, message=exc.message)
            rows.append(row)
            lab.write_json(folder / 'result.json', row)
            lab.write_json(root / 'generation-summary.json', dict(results=rows, validation='NONE', calls_reserved=len(rows)))
            if row['status'] != 'GENERATED_UNVERIFIED': return 2
    print('Original prompt sent verbatim. Outputs saved; no functional verification: ' + str(root))
    return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['_worker'])
    p.add_argument('--run-dir', required=True)
    p.add_argument('--model-dir', required=True)
    p.add_argument('--job-id', required=True)
    p.add_argument('--attempt', required=True)
    args = p.parse_args()
    raise SystemExit(worker(Path(args.run_dir).resolve(), args.model_dir, args.job_id, Path(args.attempt).resolve()))
