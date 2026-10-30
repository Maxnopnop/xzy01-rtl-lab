"""Equal-call-budget FSM study; immutable plans, two guarded turns per RTL."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import csv
import html
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import backends
import batch
import codex_adapter
import fsm_checks
import fsm_ir
import rtl_lab as lab


ROOT = batch.ROOT
ARMS = ('prose', 'table', 'checked_table')
STYLE = ('Use reg/localparam state encodings and case/if assignments for Icarus compatibility. '
         'Avoid enum-valued ternary assignments. Preserve the specified reset, overlap and cycle timing.')
NO_TOOLS = 'Do not invoke tools, read files, run tests, or delegate. Reply directly.'


def identity():
    return dict(batch.identity('dev10'), **{p: lab.digest((ROOT / p).read_bytes()) for p in
                ('fsm_study.py', 'fsm_ir.py', 'fsm_checks.py')})


def init(run, config_path, mode='codex'):
    config = batch.read(config_path)
    if config['schema'] != 1 or config['arms'] != list(ARMS):
        raise ValueError('Expected the three fixed experimental arms')
    if not 1 <= len(config['models']) <= 4 or len(set(config['models'])) != len(config['models']):
        raise ValueError('Expected 1..4 distinct model IDs')
    if not config['tasks'] or len(set(config['tasks'])) != len(config['tasks']) or set(config['tasks']) - set(fsm_checks.CONTRACTS):
        raise ValueError('Unsupported or duplicate FSM tasks')
    if type(config['repeats']) is not int or not 1 <= config['repeats'] <= 20:
        raise ValueError('repeats must be 1..20')
    if type(config['max_calls']) is not int or config['max_calls'] < 0:
        raise ValueError('Invalid call cap')
    for k in ('api_timeout', 'compile_timeout', 'sim_timeout'):
        if not isinstance(config[k], (int, float)) or not 0 < config[k] <= 600:
            raise ValueError('Timeout must be within 0..600 seconds')
    if run.exists() and any(run.iterdir()):
        raise ValueError('Choose a new/empty run directory')
    specs = {s['id']: s for s in batch.manifest('dev10')}
    jobs = []
    # Six task/model/repeat blocks per three-arm rotation; reverse model order
    # in alternate repeats. Completion order can differ with two workers.
    for sample in range(1, config['repeats'] + 1):
        for t, task in enumerate(config['tasks']):
            models = list(enumerate(config['models'], 1))
            if sample % 2 == 0:
                models.reverse()
            for m, model in models:
                offset = (sample - 1 + t + m - 1) % 3
                order = ARMS[offset:] + ARMS[:offset]
                for arm in order:
                    jobs.append(dict(id=f'm{m:02d}__{task}__{arm}__s{sample:03d}', task=task,
                                     sample=sample, arm=arm, model=model))
    config.update(mode=mode, suite='dev10', task_dir=batch.SUITES['dev10'],
                  iverilog=None, vvp=None, synthesis='none', codex_executable=None,
                  codex_reasoning=config['reasoning_effort'])
    run.mkdir(parents=True, exist_ok=True)
    plan = dict(schema=2, study='fsm48-v1', created_utc=lab.utc(), config=config,
                tasks=[specs[t] for t in config['tasks']], jobs=jobs,
                source_hashes=identity(), max_calls=config['max_calls'] if mode == 'codex' else 0,
                planned_model_calls=2 * len(jobs) if mode == 'codex' else 0,
                public_contracts={t: fsm_checks.public_contract(t) for t in config['tasks']})
    batch.atomic(run / 'plan.json', plan)
    batch.atomic(run / 'study-lock.json', dict(plan_sha256=lab.digest((run / 'plan.json').read_bytes())))
    report(run)
    print(f"Plan: {len(jobs)} RTL, {plan['planned_model_calls']} calls, cap {plan['max_calls']}, {mode}")


def read_plan(run, check_source=False):
    if lab.digest((run / 'plan.json').read_bytes()) != batch.read(run / 'study-lock.json')['plan_sha256']:
        raise ValueError('Frozen study plan changed')
    plan = batch.read(run / 'plan.json')
    if check_source:
        if identity() != plan['source_hashes']:
            raise ValueError('Study code changed; create a new run')
        batch.manifest('dev10')
    return plan


def context(spec, contract):
    return (spec['spec'] + '\n\nCommon implementation convention:\n' + STYLE +
            '\n\nPublic specification examples (same in every condition):\n' +
            json.dumps(contract, ensure_ascii=False, indent=2))


def prompts(spec, arm, contract, intermediate=None):
    common = context(spec, contract)
    if intermediate is None:
        instruction = ('Describe an ordinary prose implementation plan in at most 800 words. '
                       'Explain states, reset, transitions, and output timing. Do not output RTL or JSON.'
                       if arm == 'prose' else fsm_ir.SCHEMA_TEXT)
        return instruction + '\n\n' + common + '\n\n' + NO_TOOLS
    prompt = (lab.SYSTEM_PROMPT + '\n\n' + common + '\n\nPrevious-stage design artifact:\n' +
              intermediate + '\n\nUse the artifact to implement the specification. '
              'Resolve any contradictions in favor of the specification. Return only RTL.\n')
    if arm == 'checked_table':
        prompt += ('\nExecutable checks of the already-public contract:\n' +
                   json.dumps(fsm_checks.public_check(intermediate, spec['id']), ensure_ascii=False, indent=2) +
                   '\nCorrect any reported problems while implementing RTL; no additional model turn is available.\n')
    return prompt + '\n' + NO_TOOLS


def stage(run, folder, args, spec, name, prompt):
    """Never automatically reissue a started model call, including unknown outcomes."""
    dest = folder / name
    dest.mkdir()
    batch.atomic(dest / 'started.json', dict(started_utc=lab.utc(), model_call=args.mode == 'codex'))
    lab.write_text(dest / 'prompt.txt', prompt)
    if args.mode == 'codex':
        raw, metadata = codex_adapter.generate_text(args, dest, prompt)
    else:
        if name == 'stage1':
            raw = json.dumps(fsm_checks.reference_ir(spec['id'])['data'])
        else:
            raw = (ROOT / 'benchmarks/dev10/reference' / (spec['id'] + '.sv')).read_text(encoding='utf-8')
        metadata = dict(label='OFFLINE_FIXTURE', usage=None, codex_generation_success=False)
    lab.write_text(dest / 'response.txt', raw)
    batch.atomic(dest / 'completed.json', dict(metadata, response_sha256=lab.digest((dest / 'response.txt').read_bytes())))
    return raw


def evaluate_rtl(folder, spec, raw, intermediate, arm, tools, args):
    row = dict(ir_diagnosis=dict(status='NO_TABLE'), ir_rtl=dict(status='NOT_APPLICABLE'))
    # Private checks are run only after both generations; never feed these back.
    if arm != 'prose':
        row['ir_diagnosis'] = fsm_checks.private_check(intermediate, spec['id'])
        row['public_check'] = fsm_checks.public_check(intermediate, spec['id'])
    try:
        rtl = lab.extract_rtl(raw, spec['module'])
        lab.write_text(folder / 'dut.sv', rtl)
        row['rtl_sha256'] = lab.digest((folder / 'dut.sv').read_bytes())
        task_dir = ROOT / batch.SUITES['dev10']
        for name, expected in {spec['id'] + '_tb.sv': spec['tb_sha256'], **spec['assets']}.items():
            data = (task_dir / name).read_bytes()
            if lab.digest(data) != expected:
                raise ValueError('Fixed testbench/asset changed')
            (folder / ('testbench.sv' if name.endswith('_tb.sv') else name)).write_bytes(data)
        row.update(backends.IcarusBackend().evaluate(folder, spec, tools, args))
        if arm != 'prose' and row['ir_diagnosis']['status'] != 'IR_INVALID':
            comparison = folder / 'ir-rtl'; comparison.mkdir()
            (comparison / 'dut.sv').write_bytes((folder / 'dut.sv').read_bytes())
            bindings = fsm_checks.write_agreement_test(comparison, spec, fsm_ir.parse(intermediate),
                                                      fsm_checks.inputs_from_dev(task_dir, spec))
            row['ir_rtl'] = dict(bindings, **backends.IcarusBackend().evaluate(comparison, bindings, tools, args))
            row['ir_rtl']['mismatches'] = fsm_checks.mismatch_log(comparison)
        # Diagnostic rerun uses an independently constructed specification oracle.
        # Its result must agree with the original dev10 judge before interpretation.
        if row['status'] in ('PASS', 'FUNCTION_FAIL'):
            diagnostic = folder / 'spec-diagnostic'; diagnostic.mkdir()
            (diagnostic / 'dut.sv').write_bytes((folder / 'dut.sv').read_bytes())
            binding = fsm_checks.write_agreement_test(diagnostic, spec, fsm_checks.reference_ir(spec['id']),
                                                     fsm_checks.inputs_from_dev(task_dir, spec))
            row['spec_diagnostic'] = dict(binding, **backends.IcarusBackend().evaluate(diagnostic, binding, tools, args))
            row['spec_diagnostic']['mismatches'] = fsm_checks.mismatch_log(diagnostic)
            row['diagnostic_consistent'] = row['spec_diagnostic']['status'] == row['status']
    except lab.LabError as exc:
        row.update(status=exc.status, stage=exc.stage, message=exc.message)
    row['localization'] = fsm_ir.localize(row['ir_diagnosis']['status'], row['status'], row['ir_rtl']['status'])
    if row.get('diagnostic_consistent') is False:
        row['localization'] = 'CHECKER_INCONSISTENCY'
    return row


def worker(run, job_id):
    plan = read_plan(run, check_source=True)
    job = next(j for j in plan['jobs'] if j['id'] == job_id)
    folder = run / 'jobs' / job_id
    started = batch.read(folder / 'started.json')
    if started['reserved_calls'] != (2 if plan['config']['mode'] == 'codex' else 0):
        raise ValueError('Worker has no budget reservation')
    # A second launch cannot reuse a reservation to make additional calls.
    if any((folder / name).exists() for name in ('stage1', 'stage2', 'result.json')):
        raise ValueError('Worker already started; no automatic model retries')
    args = SimpleNamespace(**dict(plan['config'], model=job['model']))
    spec = next(s for s in plan['tasks'] if s['id'] == job['task'])
    row = dict(job_id=job_id, task=job['task'], sample=job['sample'], arm=job['arm'],
               mode=args.mode, requested_model=job['model'], directory=str(folder.relative_to(run)).replace('\\', '/'))
    start = time.monotonic()
    try:
        intermediate = stage(run, folder, args, spec, 'stage1', prompts(spec, job['arm'], plan['public_contracts'][job['task']]))
        # Bound the second-stage context without silently truncating model output.
        if len(intermediate.encode('utf-8')) > 32768:
            raise lab.LabError('EXTRACTION_ERROR', 'stage1', 'Intermediate artifact exceeds 32 KiB')
        raw = stage(run, folder, args, spec, 'stage2', prompts(spec, job['arm'], plan['public_contracts'][job['task']], intermediate))
        tools = batch.read(run / 'environment.json')['tools']
        row.update(evaluate_rtl(folder, spec, raw, intermediate, job['arm'], tools, args))
    except lab.LabError as exc:
        row.update(status=exc.status, stage=exc.stage, message=exc.message, localization='INCONCLUSIVE')
    except (ValueError, OSError, KeyError) as exc:
        row.update(status='ENV_ERROR', stage='study', message=str(exc), localization='INCONCLUSIVE')
    row['elapsed_seconds'] = round(time.monotonic() - start, 3)
    batch.atomic(folder / 'result.json', row)
    return 0


def execute(run, job, config):
    folder = run / 'jobs' / job['id']
    command = [sys.executable, str(Path(__file__).resolve()), '_worker', '--run-dir', str(run), '--job-id', job['id']]
    kwargs = dict(cwd=ROOT, env=lab.clean_env(), stdin=subprocess.DEVNULL)
    for name in ('APPDATA', 'LOCALAPPDATA', 'CODEX_HOME'):
        if name in os.environ:
            kwargs['env'][name] = os.environ[name]
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['start_new_session'] = True
    deadline = time.monotonic() + 2 * config['api_timeout'] + 3 * (config['compile_timeout'] + config['sim_timeout']) + 90
    reason = 'ENV_ERROR'
    with (folder / 'worker.log').open('wb') as log:
        proc = subprocess.Popen(command, stdout=log, stderr=log, **kwargs)
        while proc.poll() is None:
            if batch.STOP.is_set() or time.monotonic() > deadline:
                reason = 'INTERRUPTED' if batch.STOP.is_set() else 'TIMEOUT'
                batch.stop_worker(proc); break
            time.sleep(.1)
    if not (folder / 'result.json').exists():
        batch.atomic(folder / 'result.json', dict(job_id=job['id'], task=job['task'], sample=job['sample'],
            arm=job['arm'], requested_model=job['model'], mode=config['mode'], status=reason,
            stage='worker', localization='INCONCLUSIVE', message='Worker ended without a final result; no automatic retry',
            directory=str(folder.relative_to(run)).replace('\\', '/')))
    return batch.read(folder / 'result.json')


def reserve(run, job, plan):
    folder = run / 'jobs' / job['id']
    if folder.exists():
        raise ValueError('Job was already reserved; do not repeat calls')
    count = 2 if plan['config']['mode'] == 'codex' else 0
    used = sum(batch.read(p)['reserved_calls'] for p in (run / 'jobs').glob('*/started.json'))
    if used + count > plan['max_calls']:
        return False
    folder.mkdir(parents=True)
    batch.atomic(folder / 'started.json', dict(started_utc=lab.utc(), reserved_calls=count))
    return True


def run_jobs(run, workers=2, max_jobs=None):
    plan = read_plan(run, check_source=True); config = plan['config']
    if not 1 <= workers <= 2 or (max_jobs is not None and max_jobs < 0):
        raise ValueError('workers must be 1..2, max-jobs nonnegative')
    with batch.lock(run):
        tools = lab.inspect_tools(SimpleNamespace(**config), run)
        codex = None
        if config['mode'] == 'codex':
            exe = codex_adapter.find_codex(config['codex_executable'])
            codex = dict(executable=exe, sha256=lab.digest(Path(exe).read_bytes()))
            env = lab.clean_env()
            for name in ('APPDATA', 'LOCALAPPDATA', 'CODEX_HOME'):
                if name in os.environ:
                    env[name] = os.environ[name]
            auth = lab.run_process([exe, 'login', 'status'], run, 20, env)
            if auth['returncode'] or 'Logged in using ChatGPT' not in auth['stdout'] + auth['stderr']:
                raise ValueError('Existing Codex ChatGPT login required')
        environment = dict(tools=tools, codex=codex)
        if (run / 'environment.json').exists() and batch.read(run / 'environment.json') != environment:
            raise ValueError('Tool identity changed; create a new run')
        batch.atomic(run / 'environment.json', environment)
        # Interrupted reservations are terminal, not silently refunded/replayed.
        for job in plan['jobs']:
            folder = run / 'jobs' / job['id']
            if folder.exists() and not (folder / 'result.json').exists():
                batch.atomic(folder / 'result.json', dict(job_id=job['id'], task=job['task'], arm=job['arm'],
                    sample=job['sample'], requested_model=job['model'], mode=config['mode'], status='INTERRUPTED',
                    localization='INCONCLUSIVE', directory=str(folder.relative_to(run)).replace('\\', '/'),
                    message='Unknown prior outcome; reservation retained, no repeat model calls'))
        todo = [j for j in plan['jobs'] if batch.latest(run, j) is None]
        if max_jobs is not None:
            todo = todo[:max_jobs]
        batch.STOP.clear()
        old = {s: signal.signal(s, lambda *_: batch.STOP.set()) for s in (signal.SIGINT, signal.SIGTERM)}
        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                active = {}; queue = iter(todo); exhausted = False
                while active or not exhausted:
                    while len(active) < workers and not exhausted and not batch.STOP.is_set():
                        job = next(queue, None)
                        if job is None or not reserve(run, job, plan):
                            exhausted = True; break
                        active[pool.submit(execute, run, job, config)] = job
                    if batch.STOP.is_set():
                        exhausted = True
                    if not active:
                        break
                    done, _ = wait(active, timeout=.5, return_when=FIRST_COMPLETED)
                    for future in done:
                        job = active.pop(future); row = future.result()
                        summary = report(run)
                        print(f"[{summary['completed']}/{summary['planned']}] {job['id']}: {row['status']} / {row['localization']}", flush=True)
                        if row['status'] in ('API_ERROR', 'ENV_ERROR', 'INTERRUPTED', 'TIMEOUT'):
                            exhausted = True
        finally:
            for s, handler in old.items():
                signal.signal(s, handler)
            summary = report(run)
    return 0 if summary['completed'] == summary['planned'] else 1


def report(run):
    plan = read_plan(run)
    rows = [batch.latest(run, j) for j in plan['jobs']]
    rows = [r for r in rows if r is not None]
    calls = list((run / 'jobs').glob('*/stage*/started.json'))
    completed_calls = list((run / 'jobs').glob('*/stage*/completed.json'))
    tokens = Counter()
    for p in completed_calls:
        tokens.update({k: v for k, v in (batch.read(p).get('usage') or {}).items() if type(v) is int})
    groups = []
    for model in plan['config']['models']:
        for arm in ARMS:
            selected = [r for r in rows if r['requested_model'] == model and r['arm'] == arm]
            jobs = [j for j in plan['jobs'] if j['model'] == model and j['arm'] == arm]
            usage = Counter()
            for j in jobs:
                for p in (run / 'jobs' / j['id']).glob('stage*/completed.json'):
                    usage.update({k: v for k, v in (batch.read(p).get('usage') or {}).items() if type(v) is int})
            groups.append(dict(model=model, arm=arm, planned=len(jobs), completed=len(selected),
                passes=sum(r['status'] == 'PASS' for r in selected),
                counts=dict(Counter(r['status'] for r in selected)), usage=dict(usage),
                localizations=dict(Counter(r['localization'] for r in selected)),
                ir_counts=dict(Counter(r.get('ir_diagnosis', {}).get('status', 'NOT_RUN') for r in selected)),
                public_check_counts=dict(Counter(r.get('public_check', {}).get('status', 'NOT_APPLICABLE') for r in selected))))
    summary = dict(schema=1, study=plan['study'], mode=plan['config']['mode'], planned=len(plan['jobs']),
        completed=len(rows), pending=len(plan['jobs']) - len(rows), max_calls=plan['max_calls'],
        model_call_reservations=sum(batch.read(p)['reserved_calls'] for p in (run / 'jobs').glob('*/started.json')),
        model_turns_started=sum(batch.read(p)['model_call'] for p in calls),
        real_generations=sum(bool(batch.read(p).get('codex_generation_success')) for p in completed_calls),
        usage=dict(tokens), groups=groups, results=rows,
        limitations=['Two reused development tasks, two repetitions: feasibility only, no population efficacy claim.',
                    'Equal model turns, not equal tokens/compute/cost; CLI defaults and internal retries are not controlled.',
                    'IR equivalence is finite-graph exact; RTL agreement is fixed-vector simulation.',
                    've_fsm already contains a state table; it is a translation control, not NL understanding evidence.'])
    batch.atomic(run / 'summary.json', summary)
    fields = ['job_id', 'task', 'requested_model', 'arm', 'sample', 'status', 'ir_status', 'agreement', 'localization', 'rtl_sha256']
    stream = io.StringIO(newline=''); writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
    for job in plan['jobs']:
        row = next((r for r in rows if r['job_id'] == job['id']), None)
        flat = {k: (row or {}).get(k, '') for k in fields}
        flat.update(job_id=job['id'], task=job['task'], requested_model=job['model'], arm=job['arm'], sample=job['sample'],
                    status=(row or {}).get('status', 'PENDING'), ir_status=(row or {}).get('ir_diagnosis', {}).get('status', ''),
                    agreement=(row or {}).get('ir_rtl', {}).get('status', ''))
        writer.writerow(flat)
    (run / 'summary.csv').write_bytes(stream.getvalue().encode('utf-8-sig'))
    lines = ''.join('<tr>' + ''.join('<td>' + html.escape(str(g[k])) + '</td>' for k in ('model', 'arm', 'passes', 'completed', 'planned', 'localizations')) + '</tr>' for g in groups)
    lab.write_text(run / 'report.html', '<!doctype html><meta charset="utf-8"><title>FSM study</title><style>body{font:16px system-ui;margin:3em;max-width:1200px}td,th{padding:.7em;border:1px solid #ddd}table{border-collapse:collapse}</style>' +
        '<h1>FSM 预算与错误定位：可行性实验</h1><p>' + html.escape(f"{summary['completed']}/{summary['planned']} RTL，真实成功调用 {summary['real_generations']}，预留 {summary['model_call_reservations']}/{summary['max_calls']}") +
        '</p><table><tr><th>模型</th><th>条件</th><th>通过</th><th>完成</th><th>计划</th><th>诊断</th></tr>' + lines + '</table><p>' +
        '</p><p>'.join(html.escape(s) for s in summary['limitations']) + '</p>')
    return summary


def curate(run, destination):
    """Allowlisted evidence only: never account logs, auth files or workspaces."""
    summary = report(run); plan = read_plan(run)
    if summary['pending']:
        raise ValueError('Finish the study before curating evidence')
    if destination.exists():
        raise ValueError('Evidence destination exists')
    destination.mkdir(parents=True)
    for name in ('plan.json', 'study-lock.json', 'summary.json', 'summary.csv', 'report.html', 'environment.json'):
        (destination / name).write_bytes((run / name).read_bytes())
    for job in plan['jobs']:
        source = run / 'jobs' / job['id']; target = destination / 'jobs' / job['id']; target.mkdir(parents=True)
        for name in ('result.json', 'dut.sv', 'started.json'):
            if (source / name).is_file():
                (target / name).write_bytes((source / name).read_bytes())
        for stage_name in ('stage1', 'stage2'):
            stage_dir = source / stage_name
            if not stage_dir.exists():
                continue
            dst = target / stage_name; dst.mkdir()
            for name in ('prompt.txt', 'response.txt', 'started.json'):
                if (stage_dir / name).is_file():
                    (dst / name).write_bytes((stage_dir / name).read_bytes())
            if (stage_dir / 'completed.json').exists():
                meta = batch.read(stage_dir / 'completed.json')
                meta.pop('codex_thread_id', None)
                batch.atomic(dst / 'completed.json', meta)
    if (run / 'synthesis-review/summary.json').exists():
        (destination / 'synthesis-summary.json').write_bytes((run / 'synthesis-review/summary.json').read_bytes())
    hashes = {str(p.relative_to(destination)).replace('\\', '/'): lab.digest(p.read_bytes()) for p in destination.rglob('*') if p.is_file()}
    batch.atomic(destination / 'evidence-lock.json', hashes)
    print('Curated evidence: ' + str(destination))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    for name in ('init', 'run', 'report', 'curate', '_worker'):
        p = sub.add_parser(name); p.add_argument('--run-dir', required=True)
        if name == 'init':
            p.add_argument('--config', default=str(ROOT / 'experiments/fsm48.json'))
            p.add_argument('--mode', choices=('codex', 'offline'), default='codex')
        elif name == 'run':
            p.add_argument('--workers', type=int, default=2); p.add_argument('--max-jobs', type=int)
        elif name == 'curate':
            p.add_argument('--destination', required=True)
        elif name == '_worker':
            p.add_argument('--job-id', required=True)
    args = parser.parse_args(argv); run = Path(args.run_dir).resolve()
    try:
        if args.command == 'init':
            init(run, Path(args.config).resolve(), args.mode)
        elif args.command == 'run':
            return run_jobs(run, args.workers, args.max_jobs)
        elif args.command == 'report':
            summary = report(run); print(json.dumps({k: v for k, v in summary.items() if k != 'results'}, ensure_ascii=False, indent=2))
        elif args.command == 'curate':
            curate(run, Path(args.destination).resolve())
        else:
            return worker(run, args.job_id)
    except (ValueError, OSError, KeyError, lab.LabError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr); return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
