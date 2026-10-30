"""Finite byte copies and parent locks; no network or execution."""
import hashlib,json,copy
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
OLD=R/'exploration/20261028/public-rag-30-review-v1'
MID='041434e2ecaf76e26f5140a81a31104800dcd71d814c525de5951945b27120f0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def cp(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(src.read_bytes())
assert sha(OLD/'console-package-main36.json')==MID
m=read(OLD/'console-package-main36.json')
assert all(sha(OLD/n)==h for n,h in read(OLD/'packet-lock.json').items())
for n,h in m['files'].items():
 assert sha(OLD/n)==h
 cp(OLD/n,P/'inputs'/n)
cp(OLD/'console-package-main36.json',P/'inputs/parent-manifest.json')
parent={str((OLD/'console-package-main36.json').relative_to(R)):MID}
state=R/'validation/console-multimodel-20261024-v1/dispatch'/MID
for f in state.rglob('*'):
 if f.is_file():parent[f.relative_to(R).as_posix()]=sha(f)
for n in ('release.json','audit.json'):
 f=R/'validation/main36-release-20261029-v1'/n;parent[f.relative_to(R).as_posix()]=sha(f)
f=R/'validation/console-multimodel-20261024-v1/slot-reservations'/f"{m['slots'][0]['id']}.json";parent[f.relative_to(R).as_posix()]=sha(f)
assert read(state/m['slots'][0]['id']/'result.json')['status']=='UNKNOWN'
assert len(list(state.glob('*/result.json')))==1
put(P/'parent-evidence-lock.json',parent)
reuse={}
for n in ('console_bridge_v3.py','console_catalog_v3.py','console_dependencies.json','rtl_lab.py'):
 cp(R/n,P/'reuse'/n);reuse[n]={'source':n,'sha256':sha(R/n)}
f=R/'exploration/20261024/public-rag-next-executor-v1/transport.py'
assert sha(f)=='7ba1d3b47e2e471a9f11d226c65700d3cd70535b581fe7863a4fa4ed27c98524'
cp(f,P/'reuse/transport.py');reuse['transport.py']={'source':f.relative_to(R).as_posix(),'sha256':sha(f)}
put(P/'reuse-provenance.json',reuse)
slots=[]
for s in m['slots']:
 t=copy.deepcopy(s);t['parent_slot_id']=s['id'];t['id']=f"rag36b1-{s['ordinal']:03d}";t['request_sha256']=m['files'][s['request']];slots.append(t)
put(P/'batch.json',{'schema':'script-new36-v1','purpose':'DRAFT_REVIEW','name':'main36-newbatch-v1','parent_manifest_sha256':MID,'old_unknown_opportunities':1,'new_max_calls':36,'cumulative_max_opportunities':37,'slots':slots,'models':m['models'],'files':m['files'],'budget_policy':'calls_only','max_tokens':None,'max_cost_usd':None,'request_timeout_seconds':180,'automatic_retries':0,'runtime_root':str(P/'live'),'global_reservations':str(R/'validation/console-multimodel-20261024-v1/slot-reservations'),'route':{'endpoint':'https://openrouter.ai/api/v1/chat/completions','proxy_url':None},'note':'Fresh IDs explicitly authorized; old UNKNOWN not cancelled. No proxy/config changes from old36 manifest.'})
print('Prepared 36 new IDs, exact original input bytes; no release.')
