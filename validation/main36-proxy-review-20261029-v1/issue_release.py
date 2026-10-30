"""Coordinator release of the user-approved new36 only. No model/EDA call."""
import datetime, hashlib, json, socket, sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
N=R/'exploration/20261029/main36-proxy-newbatch-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def deny(*a,**k):raise AssertionError('Network forbidden during release audit')
socket.socket.connect=deny
for name in ('binding-audit.json','connect-audit.json','replay-tests.json'):
 assert read(P/name)['passed'],name
assert read(P/'replay-tests.json')['tests']==28
assert read(N/'offline-audit-r1.json')['passed']
assert read(N/'offline-audit-r1.json')['source_lock_sha256']==sha(N/'source-lock-r1.json')
assert all(sha(N/n)==h for n,h in read(N/'source-lock-r1.json').items())
assert all(sha(R/n)==h for n,h in read(P/'baseline.json').items())
sys.path.insert(0,str(N))
import runner
b=runner.verify();runner.available(b)
assert not (N/'live/RUN_STARTED.json').exists()
rel={'decision':'NEW36_PROXY_SCRIPT_EXECUTION_RELEASE','user_approved':True,
 'reviewer_thread_id':'01a12088-049c-7f32-8167-48be03bcc145',
 'user_authorization_thread_id':'01a12088-049c-7f32-8167-48be03bcc145',
 'user_authorization_text':'重新开始36次实验',
 'issued_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'bindings':runner.bindings(),'permitted_slots':[s['id'] for s in b['slots']],
 'new_max_calls':36,'cumulative_max_opportunities':38,'old_unknown_preserved':True,
 'manual_start_only':True,'budget_policy':'calls_only','automatic_retries':0,
 'request_timeout_seconds':180,'runtime_root':str(N/'live'),
 'no_token_or_currency_hard_cap':True,'no_automatic_resume_or_expansion':True,
 'old_http403_preserved':True,'explicit_proxy_url':'http://127.0.0.1:3213','direct_fallback':False,'does_not_release_old_or_300_slots':True,
 'evidence':{n:sha(P/n) for n in ('binding-audit.json','connect-audit.json','replay-tests.json','baseline.json')},
 'limitations':['Old UNKNOWN may have consumed a request and cost remains unknown.',
 'Offline synthetic tests prove mechanics, not live account/provider availability.',
 'Original same-source reference is not an independent oracle; model compute budgets are not equalized.']}
with (P/'release.json').open('x',encoding='utf-8') as f:json.dump(rel,f,ensure_ascii=False,indent=2)
assert len(runner.gate(P/'release.json')['slots'])==36
print(json.dumps({'released_new_slots':36,'cumulative_ceiling':38,'release':str(P/'release.json'),'release_sha256':sha(P/'release.json'),'model_calls':0}))

