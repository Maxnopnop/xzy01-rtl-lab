"""Three public GETs, no auth, redirect, retry or generation."""
import http.client,ssl,json,hashlib,datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent
receipts=[]
for model in ['luna','terra','sol']:
    path='/api/v1/models/openai/gpt-5.6-'+model+'/endpoints'
    target=HERE/(model+'-endpoints.json')
    if target.exists(): raise SystemExit('Existing evidence: no repeat')
    c=http.client.HTTPSConnection('127.0.0.1',3213,timeout=30,context=ssl.create_default_context())
    c.set_tunnel('openrouter.ai',443)
    receipt={'path':path,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization':False,'retries':0,'proxy':'http://127.0.0.1:3213'}
    try:
        c.request('GET',path,headers={'Accept':'application/json','Connection':'close'})
        r=c.getresponse();raw=r.read(1048577)
        target.write_bytes(raw);receipt.update(status=r.status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if r.status!=200 or len(raw)>1048576: raise RuntimeError('Stop on unexpected response')
    except Exception as e:
        receipt['error_type']=type(e).__name__;raise
    finally:
        c.close();receipts.append(receipt)
        (HERE/'catalog-receipts.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
print(json.dumps([{'model':m,'endpoints':[{k:e.get(k) for k in ['name','tag','provider_name','service_tier']} for e in json.loads((HERE/(m+'-endpoints.json')).read_bytes())['data']['endpoints']]} for m in ['luna','terra','sol']],indent=2))
