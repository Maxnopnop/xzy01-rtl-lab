"""Public catalog GET only: no authentication, generation, or retry."""
import datetime, hashlib, json, urllib.request
from pathlib import Path
P = Path(__file__).resolve().parent
assert not (P/'access.json').exists(), 'One-shot acquisition already reserved'
records = []
opener = urllib.request.build_opener(urllib.request.ProxyHandler({'https':'http://127.0.0.1:3213'}))
ids = ['openai/gpt-4o-mini','openai/gpt-4.1-mini','openai/gpt-4.1-nano','openai/gpt-5-nano','openai/gpt-5.6-luna','openai/gpt-5.6-terra','openai/gpt-5.6-sol']
def fetch(url, name):
    rec = dict(url=url, file=name, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), status='RESERVED', retries=0)
    records.append(rec)
    (P/'access.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    try:
        with opener.open(urllib.request.Request(url, headers={'User-Agent':'public-metadata-review','Accept':'application/json'}),timeout=25) as r:
            data = r.read(8*1024*1024+1)
            assert len(data)<=8*1024*1024 and r.status==200
        (P/name).write_bytes(data)
        rec.update(status='SAVED', bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        return json.loads(data)
    except Exception as e:
        rec.update(status='FAILED',error=str(e))
        return None
    finally:
        (P/'access.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
catalog = fetch('https://openrouter.ai/api/v1/models','catalog.json')
if catalog is not None:
    selected = [m for m in catalog['data'] if m['id'] in ids]
    (P/'selected-models.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
    for m in selected:
        print(json.dumps({k:m.get(k) for k in ['id','canonical_slug','context_length','pricing','expiration_date','reasoning']},ensure_ascii=False))
    for mid in ['openai/gpt-4o-mini','openai/gpt-4.1-mini','openai/gpt-5.6-luna']:
        result=fetch('https://openrouter.ai/api/v1/models/'+mid+'/endpoints',mid.split('/')[1]+'-endpoints.json')
        if result:
            print(json.dumps({'id':mid,'endpoints':[{k:e.get(k) for k in ['provider_name','name','status','context_length']} for e in result.get('data',{}).get('endpoints',[])]}))
