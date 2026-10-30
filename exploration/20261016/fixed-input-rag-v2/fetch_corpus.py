"""One bounded public-source fetch. Never retry a URL or rerun this script."""
import datetime, hashlib, json, urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ledger=[]
def save():
    (HERE/'access.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
def fetch(url,name):
    assert len(ledger)<8 and not any(x['url']==url for x in ledger)
    row={'url':url,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':name}
    ledger.append(row);save()
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'fixed-input-rag-static-preparation'})
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(1048577);row['http_status']=r.status
        assert len(raw)<=1048576
        p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        row.update(status='SAVED',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        save();return raw
    except Exception as exc:
        row.update(status='FAILED_NO_RETRY',error=type(exc).__name__);save();raise
def main():
    assert not (HERE/'access.json').exists(),'Existing visit ledger; no rerun'
    info=json.loads(fetch('https://api.github.com/repos/lowRISC/style-guides/commits/master','upstream/commit.json'))
    rev=info['sha']
    tree=json.loads(fetch(f'https://api.github.com/repos/lowRISC/style-guides/git/trees/{rev}','upstream/tree.json'))
    assert not tree.get('truncated')
    paths={r['path'] for r in tree['tree']}
    license_path=next(p for p in ('LICENSE','LICENSE.md','LICENSE.txt') if p in paths)
    for path in ('VerilogCodingStyle.md',license_path):
        fetch(f'https://raw.githubusercontent.com/lowRISC/style-guides/{rev}/{path}','upstream/'+path)
    print(json.dumps({'commit':rev,'requests':len(ledger),'license':license_path}))
if __name__=='__main__':main()
