"""At most60 one-shot public GETs, no credentials, redirects or retries."""
import json,hashlib,datetime,http.client,ssl,os
from pathlib import Path
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
for name,folder in [('A','A'),('protocol','protocol')]:
    assert all(sha(P/folder/k)==v for k,v in read(P/(name+'-lock.json')).items())
assert not (P/'B').exists(),'Fetch already started: no automatic resume/retry'
cfg=read(P/'protocol/overlay.json');seal=read(P/'A-seal.json')
assert sha(P/'A-lock.json')==seal['a_lock_sha256'] and sha(P/'protocol-lock.json')==seal['protocol_lock_sha256']
put(P/'B/start.json',{'utc':utc(),'a_seal_sha256':sha(P/'A-seal.json'),'protocol_lock_sha256':sha(P/'protocol-lock.json'),'requests_before':0})
visits=[];total=0
for row in cfg['new_candidates']:
    for kind,info in row['files'].items():
        assert len(visits)<60 and info['git_blob_sha1']
        path='/NVlabs/verilog-eval/'+cfg['dataset_commit']+'/'+info['path']
        item={'utc':utc(),'task':row['id'],'kind':kind,'url':'https://raw.githubusercontent.com'+path,'expected_git_blob':info['git_blob_sha1'],'status':'RESERVED','authorization':False}
        visits.append(item);put(P/'B/access.json',visits)
        c=http.client.HTTPSConnection('127.0.0.1',3213,timeout=30,context=ssl.create_default_context());c.set_tunnel('raw.githubusercontent.com',443)
        try:
            c.request('GET',path,headers={'Accept':'text/plain','Connection':'close','User-Agent':'fixed-static-review'})
            r=c.getresponse();raw=r.read(524289);item['http_status']=r.status
            assert r.status==200 and len(raw)<=524288
            total+=len(raw);assert total<=8388608
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            dest=P/'B/originals'/info['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
            item.update(local=str(dest.relative_to(P)).replace('\\','/'),sha256=sha(dest),actual_git_blob=blob,bytes=len(raw),status='SAVED' if blob==info['git_blob_sha1'] else 'HASH_MISMATCH')
            assert blob==info['git_blob_sha1']
        except BaseException as e:
            item.update(status='FAILED_STOP_NO_RETRY',error_type=type(e).__name__);raise
        finally:
            c.close();put(P/'B/access.json',visits)
    print(row['id']+' saved',flush=True)
put(P/'B/fetch-complete.json',{'utc':utc(),'requests':len(visits),'bytes':total,'saved':sum(r['status']=='SAVED' for r in visits),'retry':0,'model_calls':0,'eda_calls':0})
