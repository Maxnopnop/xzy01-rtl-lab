"""School Python 3.6+: verify staged bytes, manually run ONE tool, ship flat files."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    lock=json.loads((ROOT/'home-lock.json').read_text())
    for n,h in lock.items():
        if Path(n).name!=n or sha(ROOT/n)!=h:raise ValueError('HOME input changed')
    return json.loads((ROOT/'console-manifest.json').read_text())
def ship(key,shared):
    work=Path.home()/'xzy01-console-single'/key
    side=work/'console-return.json';archive=work/'console-return.zip'
    meta=json.loads(side.read_text())
    if meta['key']!=key or sha(archive)!=meta['archive_sha256']:raise ValueError('Return binding failed')
    for src,ext in ((archive,'.zip'),(side,'.json')):
        dst=shared/('return-'+key+ext)
        if dst.exists():
            if sha(dst)!=sha(src):raise ValueError('Different existing return; no overwrite')
        else:
            with dst.open('xb') as f:f.write(src.read_bytes())
        if sha(dst)!=sha(src):raise ValueError('Copy failed; retain HOME evidence')
    print('FLAT RETURN COPIED')
def main():
    manifest=verify();action=sys.argv[1] if len(sys.argv)>1 else 'check'
    if action=='check':
        print('HOME HASH VERIFIED; no tool started; dependency/constraint review required before run');return 0
    if action not in ('run','ship') or len(sys.argv)!=3:raise ValueError('Use check | run SHARE | ship SHARE')
    shared=Path(sys.argv[2]);key=manifest['key']
    if not shared.is_dir():raise ValueError('Share unavailable')
    if action=='ship':ship(key,shared);return 0
    work=Path.home()/'xzy01-console-single'/key
    if work.exists():raise ValueError('Already attempted; never rerun; inspect or ship only')
    code=subprocess.call(['bash',str(ROOT/'run-one.sh')],stdin=subprocess.DEVNULL)
    if (work/'console-return.json').is_file():ship(key,shared)
    else:print('No complete return. Keep HOME state; do not retry.')
    return code
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('STOP: '+str(exc));sys.exit(2)
