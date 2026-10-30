"""One manually requested tool; frozen inputs staged in HOME. Python 3.6+."""
import hashlib,json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    lock=json.loads((ROOT/'transfer-lock.json').read_text())
    for n,h in lock.items():
        if sha(ROOT/n)!=h:raise ValueError('Staged file changed: '+n)

def ship(key,home=None,shared=None):
    home=Path.home() if home is None else home
    shared=home/'tsclient/FYP' if shared is None else shared
    work=home/'xzy01-console-single'/key
    side=work/'console-return.json';archive=work/'console-return.zip'
    meta=json.loads(side.read_text())
    if meta['key']!=key or sha(archive)!=meta['archive_sha256']:raise ValueError('Return integrity failed')
    if not shared.is_dir():raise ValueError('FYP share unavailable; keep HOME evidence and use ship later')
    for source,ext in ((archive,'.zip'),(side,'.json')):
        target=shared/('return-'+key+ext)
        if target.exists():
            if sha(target)!=sha(source):raise ValueError('Different existing return; no overwrite')
        else:
            with target.open('xb') as f:f.write(source.read_bytes())
            if sha(target)!=sha(source):raise ValueError('Return copy hash mismatch; evidence retained in HOME')
    print('FLAT RETURN COPIED: '+str(shared/('return-'+key+'.json')))

def main():
    verify()
    action=sys.argv[1] if len(sys.argv)>1 else 'check'
    if action=='check':return subprocess.call([sys.executable,str(ROOT/'check-all.py'),str(ROOT)])
    keys=json.loads((ROOT/'tool-keys.json').read_text())
    if action not in ('run','ship') or len(sys.argv)!=3 or sys.argv[2] not in keys:raise ValueError('Use check | run TOOL | ship TOOL')
    key=keys[sys.argv[2]]
    if action=='ship':ship(key);return 0
    work=Path.home()/'xzy01-console-single'/key
    if work.exists():raise ValueError('Existing attempt: do not run again; ship only after reviewing outcome')
    code=subprocess.call(['bash',str(ROOT/key/'run-one.sh')],stdin=subprocess.DEVNULL)
    if (work/'console-return.json').is_file():ship(key)
    else:print('No return archive; retain HOME evidence and report this output. Do not retry.')
    return code

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print('STOP: '+str(e));sys.exit(2)
