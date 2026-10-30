import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((R/'validation/main36-script-review-20261029-v1/baseline.json').read_bytes())
old=R/'exploration/20261029/main36-script-newbatch-v1'
for f in (old/'live').rglob('*'):
 if f.is_file():base[f.relative_to(R).as_posix()]=sha(f)
for n in ('batch.json','runner.py','source-lock-r2.json','parent-evidence-lock.json'):
 f=old/n;base[f.relative_to(R).as_posix()]=sha(f)
for n in ('validation/main36-script-review-20261029-v1/release.json','validation/console-multimodel-20261024-v1/slot-reservations/rag36b1-001.json'):
 base[n]=sha(R/n)
assert all(sha(R/n)==h for n,h in base.items())
with (P/'baseline.json').open('x',encoding='utf-8') as f:json.dump(base,f,indent=2)
print(json.dumps({'baseline_files':len(base),'model_calls':0}))
