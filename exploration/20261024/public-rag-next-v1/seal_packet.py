import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (P/'packet-lock.json').exists()
assert read(P/'self-check.json')['status']=='OFFLINE_PREPARATION_SELF_CHECK_PASS_NOT_EXECUTION_RELEASE'
groups={}
for s in read(P/'C/slots.json'):
    raw=(P/s['request']).read_bytes();wire=s['wire_model'].encode()
    normalized=raw.replace(b'"model": "'+wire+b'"',b'"model": "MODEL_ONLY_NORMALIZED"',1)
    key=s['task']+'__'+s['condition']
    groups.setdefault(key,[]).append({'slot':s['id'],'raw_request_sha256':hashlib.sha256(raw).hexdigest(),'only_model_normalized_bytes_sha256':hashlib.sha256(normalized).hexdigest(),'messages_sha256':s['messages_sha256']})
assert all(len(g)==6 and len({r['only_model_normalized_bytes_sha256'] for r in g})==1 and len({r['messages_sha256'] for r in g})==1 for g in groups.values())
put(P/'request-byte-comparison.json',{'scope':'Prepared HTTP body bytes, not transmitted; normalize only model field, no deleted substantive fields','groups':groups,'all16_groups_equal_except_model':True})
put(P/'delivery.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FROZEN_FOR_COORDINATOR_AND_USER_REVIEW','conditional_tasks':8,'excluded_candidates':12,'planned_slots':96,'executed_slots':0,'model_calls':0,'eda_calls':0,'public_source_gets':60,'public_source_bytes':111788,'account_requests':0,'retry':0,'a_lock_sha256':sha(P/'A-lock.json'),'b_lock_sha256':sha(P/'B-lock.json'),'c_lock_sha256':sha(P/'C-lock.json'),'plan_lock_sha256':sha(P/'plan-lock.json'),'source_history_policy':'Unchanged method and old evidence; all new evidence under this independent directory','review_entry':'USER_REVIEW.md','production_ready':False})
put(P/'packet-lock.json',{p.relative_to(P).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='packet-lock.json'})
lock=read(P/'packet-lock.json');assert all(sha(P/n)==h for n,h in lock.items())
print(json.dumps({'files':len(lock),'packet_lock_sha256':sha(P/'packet-lock.json'),'verified':True,'model_calls':0,'eda_calls':0}))
