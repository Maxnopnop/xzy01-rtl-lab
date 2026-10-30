"""Seal existing finite review package, without executing preparation scripts."""
import datetime,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
assert not (P/'packet-lock.json').exists()
assert all(sha(R/n)==h for n,h in read(P/'preservation-before.json').items())
assert all(sha(P/'A'/n)==h for n,h in read(P/'prior/A-lock.json').items())
assert read(P/'offline-package-audit.json')['pass']
assert read(R/'validation/rag30-independent-review-20261028-v1/input-audit.json')['passed']
put(P/'preservation-after.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_files':read(P/'preservation-before.json'),'unchanged':True,'coordinator_input_audit_sha256':sha(R/'validation/rag30-independent-review-20261028-v1/input-audit.json')})
files={p.relative_to(P).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name not in ('packet-lock.json','delivery.json')}
put(P/'packet-lock.json',files)
put(P/'delivery.json',{'status':'FROZEN_DRAFT_REVIEW_NO_RELEASE','packet_lock_sha256':sha(P/'packet-lock.json'),'files':len(files),'recommended_manifest':'console-package-main36.json','recommended_manifest_sha256':sha(P/'console-package-main36.json'),'recommended_calls':36,'archive_manifest':'console-package.json','archive_manifest_sha256':sha(P/'console-package.json'),'archive_calls':300,'categories':{'main':3,'auxiliary':22,'do_not_execute':5},'checks':259,'model_calls':0,'embedding_calls':0,'school_calls':0,'release_created':False,'automatic_retries':0,'new_calibration_runs_after_initial30':0})
assert all(sha(P/n)==h for n,h in read(P/'packet-lock.json').items())
print(json.dumps(read(P/'delivery.json'),ensure_ascii=False))
