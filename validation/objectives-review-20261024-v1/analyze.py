"""Finite offline analysis. Stdlib only. No model, network, EDA or source writes."""
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PACKET = ROOT/'exploration/20261023/public-rag-all20-v1'
API = ROOT/'exploration/20261023/direct-api-v1'
RESULTS = ROOT/'validation/openrouter-resume198-v1/runtime/continuation/results'
EVIDENCE = {}

def read(p):
    p = Path(p)
    data = p.read_bytes()
    EVIDENCE[str(p)] = hashlib.sha256(data).hexdigest()
    return json.loads(data.decode('utf-8-sig'))

def verify_lock(p, base=None):
    entries = read(p)
    failures = []
    for name, expected in entries.items():
        q = base/name if base else Path(name)
        actual = hashlib.sha256(q.read_bytes()).hexdigest()
        EVIDENCE[str(q)] = actual
        if actual != expected:
            failures.append(str(q))
    assert not failures, failures
    return {'files': len(entries), 'all_match': True}

locks = {
    'source': verify_lock(API/'source-lock.json', API),
    'input': verify_lock(API/'input-lock.json'),
    'A': verify_lock(PACKET/'A-lock.json', PACKET/'A'),
}
records = [read(p) for p in sorted(RESULTS.glob('*.json'))]
assert len(records) == 240
assert len({r['slot'] for r in records}) == 240
by_slot = {r['slot']: r for r in records}
pairs = read(ROOT/'validation/rag-paired240-audit-v1/all120-pairs.json')
assert len(pairs) == 120
SERVICE = {'SERVICE_ERROR', 'SERVICE_PROTOCOL_ERROR'}
counts = Counter()
task_pairs = defaultdict(Counter)
for p in pairs:
    statuses = [by_slot[f"{p['task']}__{arm}__{p['model']}__{p['sample']}"]['status'] for arm in ('no_rag', 'rag')]
    assert statuses == [p['no_rag'], p['rag']]
    a, b = statuses
    if a in SERVICE or b in SERVICE:
        category = 'service_unpaired'
    elif a == b == 'REFERENCE_PASS':
        category = 'both_pass'
    elif a != 'REFERENCE_PASS' and b == 'REFERENCE_PASS':
        category = 'help'
    elif a == 'REFERENCE_PASS' and b != 'REFERENCE_PASS':
        category = 'worse'
    else:
        category = 'both_nonpass'
    assert category == p['category']
    counts[category] += 1
    task_pairs[p['task']][category] += 1

def arm_summary(rows):
    available = [r for r in rows if r['status'] not in SERVICE]
    usage = [r['usage'] for r in available if isinstance(r.get('usage'), dict)]
    result = dict(planned=len(rows), nonservice=len(available),
                  passed=sum(r['status'] == 'REFERENCE_PASS' for r in available),
                  service_failures=len(rows)-len(available), statuses=dict(Counter(r['status'] for r in rows)))
    result['reported_usage_records'] = len(usage)
    result['token_fields'] = {}
    for key in ('prompt_tokens', 'completion_tokens'):
        values = [u[key] for u in usage if isinstance(u.get(key), (int, float))]
        result['token_fields'][key] = {'records': len(values), 'sum': sum(values),
                                     'mean': sum(values)/len(values) if values else None,
                                     'missing_nonservice': len(available)-len(values)}
    return result

strata = {}
for name, predicate in [
    ('all20', lambda r: True),
    ('confirmed_clear2', lambda r: r.get('clear_subset') is True),
    ('other_static7_not_confirmed', lambda r: r.get('task_label') == 'OTHER_STATIC_ELIGIBLE_NOT_IN_CONFIRMED_SUBSET'),
]:
    rows = [r for r in records if predicate(r)]
    strata[name] = {'tasks': len({r['slot'].split('__')[0] for r in rows}), 'arms': {}}
    for model in sorted({r['requested_model'] for r in rows}):
        for arm in ('no_rag', 'rag'):
            strata[name]['arms'][model+'/'+arm] = arm_summary([r for r in rows if r['requested_model'] == model and r['slot'].split('__')[1] == arm])

STOP = set('a an the and or of to in for with on as is are be by from this that it its use using only each at after before when then do not must should'.split())
def tokens(s):
    return [t for t in re.findall(r'[a-z][a-z0-9_]*', s.lower()) if t not in STOP]
chunks = read(PACKET/'A/corpus/chunks.json')
bags = [Counter(tokens(c['section']+'\n'+c['text'])) for c in chunks]
lengths = [sum(b.values()) for b in bags]
average = sum(lengths)/len(lengths)
coverage = Counter()
selections = Counter()
retrieval_rows = []
for path in sorted((PACKET/'retrieval').glob('*.json')):
    saved = read(path)
    assert hashlib.sha256(saved['query'].encode()).hexdigest() == saved['query_sha256']
    ranked = []
    for chunk, bag, length in zip(chunks, bags, lengths):
        score = 0.0
        for word in sorted(set(tokens(saved['query']))):
            tf = bag[word]
            if tf:
                df = sum(word in b for b in bags)
                score += math.log(1+(len(chunks)-df+0.5)/(df+0.5))*tf*2.2/(tf+1.2*(1-.75+.75*length/average))
        ranked.append((chunk['id'], score))
    ranked.sort(key=lambda row: (-row[1], row[0]))
    selected = [i for i, score in ranked if score > 0][:3]
    assert selected == saved['selected_ids'], path
    prior_scores = {r['chunk_id']: r['score'] for r in saved['rankings']}
    assert all(abs(score-prior_scores[i]) < 1e-10 for i, score in ranked), path
    coverage.update(selected)
    selections[tuple(selected)] += 1
    retrieval_rows.append({'task': path.stem, 'selected_ids': selected, 'replay_match': True})
assert len(retrieval_rows) == 20

# Compare complete frozen requests, allowing ONLY the target model field to differ.
request_groups = defaultdict(list)
request_paths = [Path(p) for p in EVIDENCE if 'revised-requests' in p and p.endswith('.json')]
assert len(request_paths) == 240
for path in request_paths:
    request = read(path)
    task, arm, model, sample = path.stem.split('__')
    request.pop('model')
    request_groups[(task, arm, sample)].append(request)
assert len(request_groups) == 80
assert all(len(rows) == 3 and rows[0] == rows[1] == rows[2] for rows in request_groups.values())

changed_tasks = {t: dict(c) for t,c in task_pairs.items() if c['help'] or c['worse']}
analysis = {
    'utc': datetime.now(timezone.utc).isoformat(), 'scope': 'POST_HOC_OFFLINE_DESCRIPTIVE_ANALYSIS',
    'generation_calls': 0, 'network_requests': 0, 'eda_executions': 0,
    'locks': locks, 'frozen_request_groups_equal_except_model': 80,
    'result_count': len(records), 'counts': dict(Counter(r['status'] for r in records)),
    'pair_counts': dict(counts), 'changed_task_count': len(changed_tasks), 'changed_tasks': changed_tasks,
    'strata': strata,
    'service_failures': [{'slot': r['slot'], 'status': r['status'], 'usage': r.get('usage')} for r in records if r['status'] in SERVICE],
    'retrieval': {'replayed': 20, 'all_match': True, 'corpus_chunks': len(chunks),
                  'unique_retrieved_chunks': len(coverage), 'chunk_task_counts': dict(coverage),
                  'unique_ordered_top3': len(selections), 'tasks': retrieval_rows},
    'limitations': ['No new independent functional oracle or formal/synthesis evidence.',
                    'Task strata unchanged; other_static7 is NOT confirmed clear.',
                    'Sample index pairs are independent generations, not identical random seeds or repairs.',
                    'Post-hoc analysis, descriptive only; no causal or significance claim.',
                    'Token totals use raw fields once; reasoning is not added again; currency cost not inferred.',
                    'Prompt equality covers stored controllable requests, not unobservable provider internals.'],
}
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == sha for p,sha in EVIDENCE.items())
analysis['all_read_evidence_unchanged'] = True
analysis['read_evidence_files'] = len(EVIDENCE)
for name, obj in [('analysis.json', analysis), ('evidence-lock.json', EVIDENCE)]:
    (OUT/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k: analysis[k] for k in ['result_count','counts','pair_counts','changed_task_count','locks','read_evidence_files','all_read_evidence_unchanged']}, ensure_ascii=False))
print(json.dumps({k:v for k,v in analysis['retrieval'].items() if k != 'tasks'}, ensure_ascii=False))
for key, row in strata['all20']['arms'].items():
    print(key, json.dumps(row['token_fields']))
