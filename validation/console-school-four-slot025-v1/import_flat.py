"""Promote hash-checked flat school returns to console inbox, then collect; no EDA."""
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    records=json.loads((HERE/'records.json').read_text())
    for tool,r in records.items():
        share=Path(r['shared']).parent.parent;key=r['key']
        side=share/('return-'+key+'.json');archive=share/('return-'+key+'.zip')
        if not side.exists():print(tool+': no flat return yet');continue
        meta=json.loads(side.read_text())
        if meta['key']!=key or meta['manifest_sha256']!=r['manifest_sha256'] or sha(archive)!=meta['archive_sha256']:raise ValueError('Flat return hash/source mismatch: '+tool)
        dest=Path(r['shared'])/'inbox'/key;dest.mkdir(parents=True,exist_ok=True)
        for src,name in ((archive,'console-return.zip'),(side,'console-return.json')):
            target=dest/name
            if target.exists():
                if sha(target)!=sha(src):raise ValueError('Existing inbox differs; no overwrite')
            else:
                with target.open('xb') as f:f.write(src.read_bytes())
    return subprocess.call([sys.executable,'-B',str(HERE/'collect.py')])

if __name__=='__main__':sys.exit(main())
