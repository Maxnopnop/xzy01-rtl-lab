import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent/'direct-api-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert (H/'default-regression-exit.txt').exists()
locked=['launch.py','Start-FirstThree.ps1','route.json','routing-basis.md','luna-endpoints.json','terra-endpoints.json','sol-endpoints.json','catalog-receipts.json','audit.json','powershell-tests.json']
save(H/'launch-lock.json',{n:sha(H/n) for n in locked})
save(H/'review-bindings.json',{'decision':'NOT_RELEASED','launch_lock_sha256':sha(H/'launch-lock.json'),'source_lock_sha256':sha(B/'source-lock.json'),'input_lock_sha256':sha(B/'input-lock.json'),'route_sha256':sha(H/'route.json'),'permitted_ordinals':[1,2,3],'route_path':str(H/'route.json'),'release_path':str(B/'runtime/technical-release.json'),'metadata_evidence':[{'path':str(H/n),'sha256':sha(H/n)} for n in ['luna-endpoints.json','terra-endpoints.json','sol-endpoints.json'] ]})
old=json.loads((B/'packet-lock.json').read_bytes());assert all(sha(B/n)==v for n,v in old.items())
save(H/'final-preservation.json',{'direct_api_files':len(old),'mismatches':0,'generation':0})
save(H/'packet-lock.json',{str(p.relative_to(H)).replace('\\','/'):sha(p) for p in sorted(H.rglob('*')) if p.is_file() and p.name!='packet-lock.json'})
print('sealed; no release; '+str(len(json.loads((H/'packet-lock.json').read_bytes())))+' files')
