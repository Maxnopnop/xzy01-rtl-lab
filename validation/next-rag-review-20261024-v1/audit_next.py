"""Coordinator read-only source audit; writes only its own audit receipt. No network/EDA/model."""
import hashlib, json, math, re
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
LAB = OUT.parents[1]
NEW = LAB / 'exploration/20261024/public-rag-next-v1'
OLD = LAB / 'exploration/20261023/public-rag-all20-v1'
evidence = {}
def raw(p):
    b = p.read_bytes()
    evidence[str(p)] = hashlib.sha256(b).hexdigest()
    return b
def read(p): return json.loads(raw(p))
def check_lock(p, base):
    d = read(p)
    for rel, h in d.items():
        assert hashlib.sha256(raw(base / rel)).hexdigest() == h, rel
    return len(d)

a_count = check_lock(NEW/'A-lock.json', NEW/'A')
assert raw(NEW/'A-lock.json') == raw(OLD/'A-lock.json')
for rel in read(NEW/'A-lock.json'):
    assert raw(NEW/'A'/rel) == raw(OLD/'A'/rel), rel
protocol_count = check_lock(NEW/'protocol-lock.json', NEW/'protocol')
seal = read(NEW/'A-seal.json')
start = read(NEW/'B/start.json')
end = read(NEW/'B/fetch-complete.json')
overlay = read(NEW/'protocol/overlay.json')
assert seal['frozen_utc'] < start['utc'] < end['utc']
assert hashlib.sha256(raw(NEW/'A-seal.json')).hexdigest() == start['a_seal_sha256']
assert end['requests'] == end['saved'] == 60
assert end['retry'] == end['model_calls'] == end['eda_calls'] == 0
assert len(overlay['new_candidates']) == 20
assert [r['id'] for r in overlay['new_candidates']] == overlay['remaining_ordered_ids'][:20]
blob_count = 0
for row in overlay['new_candidates']:
    assert row['order_sha256'] == hashlib.sha256((overlay['seed']+'\n'+row['id']).encode()).hexdigest()
    for spec in row['files'].values():
        b = raw(NEW/'B/originals'/spec['path'])
        got = hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        assert got == spec['git_blob_sha1'], spec['path']
        blob_count += 1
receipt = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'SOURCE_AND_METHOD_ONLY_C_PACKET_NOT_YET_AUDITED',
    'A_files_byte_identical_to_previous': a_count,
    'protocol_files_hash_match': protocol_count,
    'original_files_git_blob_match': blob_count,
    'candidate_count': 20,
    'A_sealed_before_B_fetch': True,
    'model_calls': 0, 'network_requests': 0, 'eda_executions': 0,
    'execution_release': False,
}
if (NEW/'C-seal.json').exists():
    b_count = check_lock(NEW/'B-lock.json', NEW/'B')
    c_count = check_lock(NEW/'C-lock.json', NEW/'C')
    plan_count = check_lock(NEW/'plan-lock.json', NEW)
    bseal, cseal = read(NEW/'B-seal.json'), read(NEW/'C-seal.json')
    cstart = read(NEW/'C/start.json')
    assert end['utc'] < bseal['frozen_utc'] < cstart['utc'] < cseal['frozen_utc']
    selection = read(NEW/'B/selection.json')
    ids = selection['selected_ids']
    assert ids == [r['id'] for r in selection['rows'] if r['eligible']][:12]
    chunks = read(NEW/'A/corpus/chunks.json')
    stop = set('a an the and or of to in for with on as is are be by from this that it its use using only each at after before when then do not must should'.split())
    def tokens(s): return [w for w in re.findall(r'[a-z][a-z0-9_]*',s.lower()) if w not in stop]
    bags = [Counter(tokens(c['section']+'\n'+c['text'])) for c in chunks]
    lengths = [sum(b.values()) for b in bags]
    average = sum(lengths)/len(lengths)
    system = raw(NEW/'A/system.txt').decode('utf-8')
    template = raw(NEW/'A/context-template.txt').decode('utf-8-sig')
    expected_messages = {}
    for task in ids:
        query = raw(NEW/'B/originals/dataset_spec-to-rtl'/f'{task}_prompt.txt').decode('utf-8')
        saved = read(NEW/'C/retrieval'/f'{task}.json')
        assert saved['query'] == query
        ranking = []
        for chunk, bag, length in zip(chunks,bags,lengths):
            score = 0.
            for word in sorted(set(tokens(query))):
                tf = bag[word]
                if tf:
                    df = sum(word in b for b in bags)
                    score += math.log(1+(len(chunks)-df+.5)/(df+.5))*tf*2.2/(tf+1.2*(.25+.75*length/average))
            ranking.append((chunk['id'],score))
        ranking.sort(key=lambda x:(-x[1],x[0]))
        chosen = [i for i,s in ranking if s>0][:3]
        assert chosen == saved['selected_ids'], task
        actual_scores = {r['chunk_id']:r['score'] for r in saved['rankings']}
        assert all(abs(s-actual_scores[i])<1e-10 for i,s in ranking)
        selected = [next(c for c in chunks if c['id']==i) for i in chosen]
        fragments = '\n\n'.join(f"[{c['id']}; {c['section']}; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in selected)
        context = template.format(fragments=fragments) if selected else ''
        assert raw(NEW/'C/contexts'/f'{task}.txt').decode()==context
        for condition in ('no_rag','rag'):
            expected_messages[task,condition] = [{'role':'system','content':system},{'role':'user','content':query+(context if condition=='rag' else '')}]
    slots = read(NEW/'C/slots.json')
    assert len(slots)==len(ids)*12
    groups = defaultdict(list)
    for ordinal,slot in enumerate(slots,1):
        assert slot['ordinal']==ordinal and slot['status']=='NOT_STARTED' and not slot['reserved']
        req = read(NEW/slot['request'])
        assert req['model']==slot['wire_model']=='openai/'+slot['model']
        assert req['messages']==expected_messages[slot['task'],slot['condition']]
        assert hashlib.sha256(raw(NEW/slot['request'])).hexdigest()==slot['request_sha256']
        req.pop('model')
        groups[slot['task'],slot['condition'],slot['sample']].append(req)
    assert all(len(v)==3 and v[0]==v[1]==v[2] for v in groups.values())
    receipt.update(scope='FROZEN_A_B_C_PACKET_OFFLINE_AUDIT',B_hash_files=b_count,C_hash_files=c_count,
        plan_hash_files=plan_count,selected_tasks=ids,retrievals_independently_recomputed=len(ids),
        complete_payload_groups_equal_except_model=len(groups),planned_not_started_slots=len(slots),
        A_B_C_order_matches=True,independent_oracle_established=False)
if (NEW/'packet-lock.json').exists():
    receipt['final_packet_hash_files'] = check_lock(NEW/'packet-lock.json',NEW)
    delivery = read(NEW/'delivery.json')
    assert delivery['executed_slots']==0 and delivery['production_ready'] is False
    receipt['delivery_status'] = delivery['status']
(OUT/'new-source-audit.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
(OUT/'new-source-evidence-lock.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt,indent=2))
