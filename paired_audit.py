"""Read-only evidence audit and descriptive analysis; never issues model calls."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import batch
import paired_bank as bank
import paired_study as study
import rtl_lab as lab

INFRA = {'API_ERROR', 'ENV_ERROR', 'INTERRUPTED', 'TIMEOUT'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pair_counts(rows):
    counts = Counter()
    for pair in dict.fromkeys(r['pair_id'] for r in rows):
        selected = {r['arm']: r for r in rows if r['pair_id'] == pair}
        if set(selected) != set(study.ARMS) or any(r['status'] in INFRA for r in selected.values()):
            counts['infrastructure_incomplete'] += 1
            continue
        a, b = (selected[k]['status'] == 'PASS' for k in study.ARMS)
        counts['both_pass' if a and b else 'feedback_only' if b else 'control_only' if a else 'both_functionally_fail'] += 1
    return dict(counts)


def describe(rows):
    groups = []
    for model in study.MODELS:
        for arm in study.ARMS:
            selected = [r for r in rows if r['requested_model'] == model and r['arm'] == arm]
            groups.append(dict(model=model, arm=arm, planned=len(selected),
                passes=sum(r['status'] == 'PASS' for r in selected),
                infrastructure_missing=sum(r['status'] in INFRA for r in selected),
                functional_observations=sum(r['status'] not in INFRA for r in selected),
                statuses=dict(Counter(r['status'] for r in selected))))
    return dict(groups=groups, pairs=pair_counts(rows))


def audit(folder):
    folder = Path(folder)
    lock = batch.read(folder/'evidence-lock.json')
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name != 'evidence-lock.json'}
    require(actual == set(lock), 'Evidence file inventory changed')
    for name, expected in lock.items():
        target = (folder/name).resolve()
        require(target.is_relative_to(folder.resolve()), 'Unsafe evidence path')
        require(lab.digest(target.read_bytes()) == expected, 'Evidence changed: '+name)
    plan = study.read_plan(folder, True)
    summary = batch.read(folder/'summary.json')
    synth = batch.read(folder/'synthesis-summary.json')
    require(not summary['pending'], 'Incomplete plan')
    require(summary['planned'] == summary['completed'] == len(plan['jobs']), 'Slot count mismatch')
    require(len({r['job_id'] for r in summary['results']}) == len(plan['jobs']), 'Duplicate/missing result')
    require(len(synth['results']) == len(plan['jobs']), 'Synthesis count mismatch')
    require(len({r['job_id'] for r in synth['results']}) == len(plan['jobs']), 'Duplicate synthesis result')
    require(batch.read(folder/'synthesis-environment.json')['plan_sha256'] == lab.digest((folder/'plan.json').read_bytes()), 'Synthesis plan mismatch')
    rows = []; usage = Counter(); reservations = started = outputs = 0
    for job in plan['jobs']:
        require(job['task'] not in bank.HELDOUT, 'Held-out task was model-evaluated')
        root = folder/'jobs'/job['id']
        row = batch.read(root/'result.json')
        require(row == next(r for r in summary['results'] if r['job_id'] == job['id']), 'Summary row mismatch')
        reservations += batch.read(root/'started.json')['reserved_calls']
        started += int(batch.read(root/'call/started.json')['model_call'])
        case = next(c for c in plan['cases'] if c['id'] == job['case'])
        spec = next(s for s in plan['tasks'] if s['id'] == job['task'])
        raw = (bank.ROOT/case['ir_file']).read_text(encoding='utf-8')
        require((root/'call/prompt.txt').read_text(encoding='utf-8') == study.prompt(spec, raw, job['arm']), 'Prompt changed')
        syn = next(r for r in synth['results'] if r['job_id'] == job['id'])
        require(syn['source_result_sha256'] == lab.digest((root/'result.json').read_bytes()), 'Synthesis result binding mismatch')
        require(syn['rtl_sha256'] == row.get('rtl_sha256') and syn['simulation_status'] == row['status'], 'Synthesis DUT/status mismatch')
        if (root/'call/completed.json').exists():
            meta = batch.read(root/'call/completed.json')
            require(meta['codex_generation_success'] and meta['tools_used'] is False, 'Invalid generation evidence')
            require('codex_thread_id' not in meta, 'Uncurated session ID')
            require(lab.digest((root/'call/response.txt').read_bytes()) == meta['response_sha256'], 'Response changed')
            outputs += 1
            usage.update({k:v for k,v in (meta.get('usage') or {}).items() if type(v) is int})
        if row.get('rtl_sha256'):
            require(lab.digest((root/'dut.sv').read_bytes()) == row['rtl_sha256'], 'DUT changed')
            require(syn['status'] == 'SYNTH_PASS', 'Retained DUT did not pass synthesis')
            require(row.get('diagnostic_consistent') is True, 'Judge inconsistency')
            require(row['ir_diagnosis']['status'] == 'IR_SPEC_MISMATCH', 'Initial IR is not erroneous')
            require(row['ir_sha256'] == case['ir_sha256'], 'Initial IR binding changed')
        else:
            require(syn['status'] == 'NOT_RUN', 'Missing DUT falsely synthesized')
        rows.append(dict(row, case_kind=case['kind'], error_type=case['error_type']))
    require(reservations == started == summary['model_call_reservations'] == summary['model_turns_started'] == plan['max_calls'], 'Call budget mismatch')
    require(outputs == summary['real_generations'], 'Observed generation count mismatch')
    with (folder/'summary.csv').open(encoding='utf-8-sig', newline='') as stream:
        csv_rows = list(csv.DictReader(stream))
    require(len(csv_rows) == len(rows), 'CSV row count mismatch')
    require({r['job_id']:r['status'] for r in csv_rows} == {r['job_id']:r['status'] for r in rows}, 'CSV status mismatch')
    return dict(stage=plan['stage'], evidence=folder.name, verified_files=len(lock),
        plan_sha256=lab.digest((folder/'plan.json').read_bytes()),
        planned=len(rows), reserved_calls=reservations, started_calls=started, observed_generations=outputs,
        usage_of_observed_generations=dict(usage), synthesis_counts=synth['counts'],
        by_model=describe(rows),
        by_kind={k:describe([r for r in rows if r['case_kind']==k]) for k in sorted({r['case_kind'] for r in rows})},
        by_task={k:describe([r for r in rows if r['task']==k]) for k in sorted({r['task'] for r in rows})},
        by_error_type={k:describe([r for r in rows if r['error_type']==k]) for k in sorted({r['error_type'] for r in rows})},
        nonpasses=[dict(job_id=r['job_id'],status=r['status'],localization=r['localization']) for r in rows if r['status']!='PASS'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',nargs='+',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:
        results=[audit(p) for p in args.evidence]
        require([r['stage'] for r in results]==['A','B'], 'Supply A then B')
        a,b=map(Path,args.evidence)
        gate=batch.read(b/'plan.json')['expansion_gate']
        require(gate['stage_a_plan_sha256']==results[0]['plan_sha256'] and gate['stage_a_summary_sha256']==lab.digest((a/'summary.json').read_bytes()), 'Expansion gate binding mismatch')
        require(sum(r['reserved_calls'] for r in results)==gate['total_campaign_cap']==96,'Campaign cap mismatch')
        output=dict(schema=1,kind='POSTHOC_READ_ONLY_EVIDENCE_AUDIT',stages=results,
            limitations=['Infrastructure-incomplete pairs are separate from functional failures.',
                'Usage of the two unknown timed-out calls is unavailable, not zero.',
                'Descriptive results only; no independent-task population inference.',
                'Current frozen runtime source is checked; use its recorded revision for future replay.'])
        batch.atomic(Path(args.output),output)
        print(json.dumps({r['stage']:dict(planned=r['planned'],observed=r['observed_generations'],pairs=r['by_model']['pairs'],usage=r['usage_of_observed_generations']) for r in results},indent=2))
    except (ValueError,OSError,KeyError,StopIteration) as exc:
        parser.exit(1,'AUDIT FAILED: '+str(exc)+'\n')


if __name__=='__main__': main()
