"""Finalize only this new review directory; no execution authorization."""
import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    assert not p.exists(),p
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=json.loads((P/'audit.json').read_bytes());assert audit['passed']
for stage in ['A','B','C','protocol']:
    lock=json.loads((P/(stage+'-lock.json')).read_bytes())
    assert all(sha(P/stage/n)==h for n,h in lock.items())
assert not(P/'runtime').exists()
lock={f.relative_to(P).as_posix():sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name not in ['packet-lock.json','delivery.json']}
put(P/'packet-lock.json',lock)
put(P/'delivery.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PREPARED_NOT_RELEASED_PENDING_INDEPENDENT_REVIEW','entry':'USER_REVIEW.md','packet_files':len(lock),'packet_lock_sha256':sha(P/'packet-lock.json'),'conditional_tasks':2,'excluded_candidates':18,'candidate_count':20,'retrievals':2,'not_started_slots':24,'executed_slots':0,'model_calls':0,'eda_calls':0,'audit_checks':22,'historical_hash_matches':2647,'independent_correctness':'NOT_ESTABLISHED','delivery_receipt_self_excluded_from_packet':True})
assert all(sha(P/n)==h for n,h in lock.items())
print((P/'delivery.json').read_text())
