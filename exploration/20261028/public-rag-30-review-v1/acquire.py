"""Bounded source acquisition; cache first, at most30 GET, no retry/resume."""
import datetime,hashlib,http.client,json,ssl,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
scope=json.loads((P/'scope.json').read_bytes());seal=json.loads((P/'scope-seal.json').read_bytes());assert sha((P/'scope.json').read_bytes())==seal['scope_sha256']
assert not (P/'acquisition.json').exists(),'Already attempted; no retry/resume'
names=subprocess.run(['rg','--files','--hidden','--no-ignore',str(R/'exploration')],capture_output=True,text=True,check=True).stdout.splitlines()
index={}
for n in sorted(names):
 f=Path(n)
 if P not in f.parents:index.setdefault(f.name,[]).append(f)
records=[];get_count=0
for row in scope['tasks']:
 for kind,meta in row['files'].items():
  rec={'task':row['id'],'kind':kind,'url':f"https://raw.githubusercontent.com/NVlabs/verilog-eval/{scope['commit']}/{meta['path']}",'expected_git_blob':meta['git_blob_sha1'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'STARTED','retries':0};records.append(rec);put(P/'acquisition.json',records)
  raw=None
  for f in index.get(row['id']+'_'+kind,[]):
   content=f.read_bytes()
   if blob(content)==meta['git_blob_sha1']:
    raw=content;rec.update(source='LOCAL_CACHE',cache_path=str(f),historically_present=True);break
  if raw is None:
   if row['prior_adopted']:raise RuntimeError('Old adopted source missing; stop')
   assert get_count<30;get_count+=1;rec.update(source='PUBLIC_GET',request_ordinal=get_count,status='RESERVED_BEFORE_GET');put(P/'acquisition.json',records)
   conn=http.client.HTTPSConnection('127.0.0.1',3213,timeout=25,context=ssl.create_default_context());conn.set_tunnel('raw.githubusercontent.com',443)
   try:
    conn.request('GET',rec['url'].split('raw.githubusercontent.com')[1],headers={'Accept':'text/plain','User-Agent':'finite-source-review','Connection':'close'})
    res=conn.getresponse();raw=res.read(524289);rec['http_status']=res.status
    assert res.status==200 and len(raw)<=524288
   except BaseException as e:
    rec.update(status='FAILED_STOP_NO_RETRY',error_type=type(e).__name__);put(P/'acquisition.json',records);raise
   finally:conn.close()
  assert blob(raw)==meta['git_blob_sha1']
  dest=P/'originals'/meta['path'];dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw)
  rec.update(status='SAVED',local=dest.relative_to(P).as_posix(),sha256=sha(raw),actual_git_blob=blob(raw),bytes=len(raw));put(P/'acquisition.json',records)
 print(row['id'],flush=True)
put(P/'acquisition-summary.json',{'files':len(records),'GETs':get_count,'cache_files':sum(r['source']=='LOCAL_CACHE' for r in records),'retry':0,'model_calls':0,'scope_sha256':seal['scope_sha256']})
