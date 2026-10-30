"""Copy reviewed r2 infrastructure; change only identity/budget/proxy bindings."""
import json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];S=P.parent/'main36-script-newbatch-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def copy(a,b):
 b.parent.mkdir(parents=True,exist_ok=True)
 with b.open('xb') as f:f.write(a.read_bytes())
assert all(sha(S/n)==h for n,h in read(S/'source-lock-r2.json').items())
for d in ('inputs','reuse'):
 for f in (S/d).rglob('*'):
  if f.is_file() and '__pycache__' not in str(f):copy(f,P/f.relative_to(S))
for n in ('tool-discovery.json','reuse-provenance.json','test_entry.ps1'):copy(S/n,P/n)
for n in ('runner.py','tests.py','lock_source.py','Start-Experiments.ps1'):
 text=(S/n).read_text(encoding='utf-8').replace('source-lock-r2','source-lock-r1').replace('offline-audit-r2','offline-audit-r1').replace('test-output-r2','test-output-r1').replace("T=P/'offline-r2'","T=P/'offline-r1'")
 text=text.replace('rag36b1-', 'rag36p1-').replace('NEW36_SCRIPT_EXECUTION_RELEASE','NEW36_PROXY_SCRIPT_EXECUTION_RELEASE')
 text=text.replace("'cumulative_max_opportunities']==37","'cumulative_max_opportunities']==38").replace("'cumulative_max_opportunities')==37","'cumulative_max_opportunities')==38").replace("'cumulative_max_opportunities':37","'cumulative_max_opportunities':38")
 text=text.replace("'old_unknown':1,'new_max_calls'","'old_unknown':1,'old_http_error':1,'new_max_calls'").replace("'total_reserved_including_old':1+reserved","'total_reserved_including_old':2+reserved")
 text=text.replace("self.assertEqual(r['total_reserved_including_old'],37)","self.assertEqual(r['total_reserved_including_old'],38)")
 text=text.replace('cumulative 37 opportunities','cumulative 38 opportunities')
 text=text.replace("{'endpoint':bridge.ENDPOINT,'proxy_url':None}","{'endpoint':bridge.ENDPOINT,'proxy_url':'http://127.0.0.1:3213'}")
 with (P/n).open('x',encoding='utf-8') as f:f.write(text)
b=read(S/'batch.json');b.update(schema='script-proxy-new36-v1',name='main36-proxy-newbatch-v1',old_unknown_opportunities=1,old_http_error_opportunities=1,cumulative_max_opportunities=38,runtime_root=str(P/'live'),route={'endpoint':'https://openrouter.ai/api/v1/chat/completions','proxy_url':'http://127.0.0.1:3213'},note='Explicit user-approved new36, old UNKNOWN+403 retained; sole transport change explicit HTTP CONNECT Astrill 127.0.0.1:3213, no direct fallback.')
mapping=[]
for s in b['slots']:
 old=s['id'];s['id']=f"rag36p1-{s['ordinal']:03d}"
 mapping.append({'id':s['id'],'previous_script_slot_id':old,'original_slot_id':s['parent_slot_id'],'request_sha256':s['request_sha256']})
put(P/'slot-mapping.json',mapping);put(P/'batch.json',b)
put(P/'route-config.json',{'endpoint':b['route']['endpoint'],'api_key_env':'OPENROUTER_API_KEY','proxy_url':b['route']['proxy_url'],'proxy_env':None,'provider_only':['openai'],'expected_provider':'OpenAI'})
parent=read(S/'parent-evidence-lock.json')
for f in (S/'live').rglob('*'):
 if f.is_file():parent[f.relative_to(R).as_posix()]=sha(f)
for n in ('batch.json','source-lock-r2.json','offline-audit-r2.json'):
 parent[(S/n).relative_to(R).as_posix()]=sha(S/n)
for n in ('release.json','REPORT.md'):
 f=R/'validation/main36-script-review-20261029-v1'/n;parent[f.relative_to(R).as_posix()]=sha(f)
f=R/'validation/console-multimodel-20261024-v1/slot-reservations/rag36b1-001.json';parent[f.relative_to(R).as_posix()]=sha(f)
assert read(S/'live/jobs/001/result.json')['status']=='HTTP_ERROR'
assert read(S/'live/jobs/001/transport-response.json')['http_status']==403
assert len(list((S/'live').glob('jobs/*/reservation.json')))==1
put(P/'parent-evidence-lock.json',parent)
put(P/'migration-provenance.json',{'from':str(S),'source_lock_sha256':sha(S/'source-lock-r2.json'),'old_parent_files':len(parent),'new_calls':36,'cumulative_max':38,'changes':['new batch IDs and locks','old UNKNOWN+403 budget accounting','explicit HTTP CONNECT proxy, no fallback'],'no_original_files_modified':True})
print('Prepared new36 proxy identity; no network and no release.')
