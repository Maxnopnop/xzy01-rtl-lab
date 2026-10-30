"""Finite public source acquisition only. No model routes, auth, or retry."""
import json,urllib.request,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent
assert not(P/'access.json').exists()
records=[]
opener=urllib.request.build_opener(urllib.request.ProxyHandler({'http':'http://127.0.0.1:3213','https':'http://127.0.0.1:3213'}))
def fetch(url,name):
    r={'url':url,'local':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'RESERVED','retry':0};records.append(r)
    (P/'access.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    try:
        with opener.open(urllib.request.Request(url,headers={'User-Agent':'public-source-review','Accept':'application/vnd.github+json'}),timeout=30) as response:
            data=response.read(1048577)
            assert len(data)<=1048576
            assert response.status==200
        dest=P/name;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();dest.write_bytes(data)
        r.update(status='SAVED',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        return data
    except Exception as e:
        r.update(status='FAILED',error=repr(e));raise
    finally:(P/'access.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
commit=json.loads(fetch('https://api.github.com/repos/dorianbrown/rank_bm25/commits/master','upstream/commit.json'))['sha']
for name in ['rank_bm25.py','LICENSE','README.md']:fetch(f'https://raw.githubusercontent.com/dorianbrown/rank_bm25/{commit}/{name}','upstream/'+name)
print(json.dumps({'commit':commit,'requests':len(records),'bytes':sum(x.get('bytes',0) for x in records),'retry':0}))
