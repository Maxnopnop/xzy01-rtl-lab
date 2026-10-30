"""Read-only provenance audit; writes a new audit, never experiment evidence."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'exploration/20261011/runs'

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

audit = {'date': '2026-10-16', 'scope': 'Existing evidence only; zero model/tool reruns', 'runs': {}}
for run in ['r1b-v2', 'timed-reset-v1']:
    selection = BASE / run / 'selection.json'
    rows = read(selection)['rows']
    details = []
    counts = Counter()
    for row in rows:
        result = ROOT / row['result_path']
        obj = read(result)
        job = result.parent
        origin = result.parts[-4]
        stages = ['stage1', 'stage2'] if origin == 'fsm48' else ['call']
        other = job.with_name(('m02' if job.name.startswith('m01') else 'm01') + job.name[3:])
        checks = {'result_hash': sha(result) == row['result_sha256'],
                  'rtl_hash': sha(job / 'dut.sv') == row['rtl_sha256']}
        prompts = []
        for stage in stages:
            d = job / stage
            meta = read(d / 'completed.json')
            checks[stage + '_response_hash'] = sha(d / 'response.txt') == meta['response_sha256']
            checks[stage + '_generation_success'] = meta.get('codex_generation_success') is True
            other_prompt = other / stage / 'prompt.txt'
            prompts.append({'stage': stage, 'sha256': sha(d / 'prompt.txt'),
                            'other_model_prompt': str(other_prompt.relative_to(ROOT)),
                            'same_bytes': sha(other_prompt) == sha(d / 'prompt.txt') if other_prompt.exists() else None})
        raw = (job / stages[-1] / 'response.txt').read_text(encoding='utf-8')
        fences = re.findall(r'```[^\n]*\n(.*?)```', raw, re.S)
        extracted = (fences[0] if fences else raw).strip() + '\n'
        checks['extracted_rtl_matches'] = extracted == (job / 'dut.sv').read_text(encoding='utf-8')
        prompt = (job / stages[-1] / 'prompt.txt').read_text(encoding='utf-8')
        category = 'two_stage_' + obj['arm'] if origin == 'fsm48' else 'one_call_candidate_IR_' + obj['arm']
        counts[category] += 1
        details.append({'result': str(result.relative_to(ROOT)), 'category': category,
                        'original_status': obj['status'], 'checks': checks, 'prompts': prompts,
                        'contains_candidate_ir': 'Candidate intermediate state table' in prompt,
                        'strict_spec_only_direct_baseline': False})
    hist = read(BASE / run / 'history-results.json')
    if run == 'r1b-v2':
        statuses = Counter(x['status'] for h in hist for x in h['results'])
        replays = Counter(x['witness']['status'] for h in hist for x in h['results'] if 'witness' in x)
    else:
        statuses = Counter(h['result']['status'] for h in hist)
        replays = Counter()
    audit['runs'][run] = {'selection_sha256': sha(selection), 'n': len(rows),
                         'categories': dict(counts), 'all_provenance_checks_pass': all(all(d['checks'].values()) for d in details),
                         'validation_statuses': dict(statuses), 'witness_statuses': dict(replays), 'rows': details}
out = ROOT / 'validation/r1bc_prompt_provenance_20261016.json'
out.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: {a:b for a,b in v.items() if a != 'rows'} for k,v in audit['runs'].items()}, indent=2))
