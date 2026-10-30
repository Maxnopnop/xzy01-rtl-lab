"""Python 3.6+; one manually launched school case, never a scheduler."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import subprocess
import sys
import time
import zipfile

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,obj):
    with Path(p).open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2)

def verify(root):
    manifest=read(root/'console-manifest.json')
    for name,h in manifest['inputs'].items():
        if Path(name).name!=name or sha(root/name)!=h:raise ValueError('Input hash mismatch')
    return manifest

def verdict(text,code,expected):
    matches=re.findall(r'^Mismatches: (\d+) in (\d+) samples$',text,re.M)
    if code!=0 or len(matches)!=1 or 'TIMEOUT' in text.upper():return dict(status='TOOL_OR_RECEIPT_ERROR')
    errors,count=map(int,matches[0])
    return dict(status=('FIXED_TEST_PASS' if errors==0 else 'FUNCTION_FAIL') if count==expected else 'CHECK_COUNT_DIFFERENT',mismatches=errors,samples=count,expected_samples=expected)

def ship(work,share):
    meta=read(work/'console-return.json');archive=work/'console-return.zip'
    if sha(archive)!=meta['archive_sha256']:raise ValueError('Return changed')
    dest=share
    if not dest.is_dir():raise ValueError('Shared root unavailable; retain HOME return')
    for src in (archive,work/'console-return.json'):
        p=dest/('return-'+meta['key']+src.suffix)
        if p.exists():
            if sha(p)!=sha(src):raise ValueError('Different prior return')
        else:
            with p.open('xb') as f:f.write(src.read_bytes())
    print('RETURN COPIED: '+str(dest))

def execute(manifest,work,started):
    tool=manifest["tool"]
    if tool in ('dc','genus'):
        sys.path.insert(0,str(work))
        import ece_synth_school
        code=ece_synth_school.run(work)
        status='COMPLETED_REVIEW_REQUIRED' if code==0 else 'SYNTHESIS_TOOL_ERROR'
        result=dict(status=status,returncode=code)
    else:
        with (work/'launcher.log').open('wb') as log:
            p=subprocess.Popen(['tcsh','-f','run.csh'],cwd=str(work),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            limit=None
            try:
                while p.poll() is None:
                    sizes=[x.stat().st_size for x in work.rglob('*') if x.is_file() and not x.is_symlink()]
                    if time.time()-started>600:limit='TIMEOUT'
                    elif sum(sizes)>128*1024**2 or log.tell()>16*1024**2:limit='RESOURCE_LIMIT'
                    if limit:os.killpg(p.pid,signal.SIGKILL);p.wait();break
                    time.sleep(.25)
            finally:
                if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
        text=(work/'simulate.log').read_text(errors='replace') if (work/'simulate.log').exists() else ''
        result=dict(status=limit) if limit else verdict(text,p.returncode,manifest['expected_checks'])
        result['returncode']=p.returncode
    return result

def school_host():return os.name=='posix'

def main():
    root=Path(__file__).resolve().parent
    manifest=verify(root);key=manifest['key']
    if not re.fullmatch(r'console-[a-f0-9]{16}',key):raise ValueError('Invalid key')
    if len(sys.argv)!=3 or sys.argv[1] not in ('run','ship'):raise ValueError('Explicit run|ship and shared root required')
    share=Path(sys.argv[2]).resolve()
    if root.parent!=Path.home().resolve()/'xzy01-console-v3-homefix-v1':raise ValueError('Stage to HOME before execution')
    work=Path.home()/'xzy01-console-single'/key
    if len(sys.argv)>1 and sys.argv[1]=='ship':ship(work,share);return 0
    if not school_host():raise ValueError('School Linux only')
    work.mkdir(parents=True,exist_ok=False) # never repeat same case after unknown outcome
    for name in list(manifest['inputs'])+['console-manifest.json']:
        shutil.copyfile(str(root/name),str(work/name))
    tool=manifest['tool'];started=time.time()
    try:
        result=execute(manifest,work,started)
    except Exception as exc:
        result=dict(status='ENVIRONMENT_ERROR',error_type=type(exc).__name__,returncode=None)
    try:verify(work)
    except Exception:result=dict(status='EVIDENCE_ERROR',returncode=None)
    save(work/'console-result.json',dict(result,elapsed_seconds=time.time()-started,key=key,manifest_sha256=sha(root/'console-manifest.json')))
    allowed=set(manifest['inputs'])|{'console-manifest.json','console-result.json','launcher.log','simulate.log','compile.log','tool_version.log','simulate.exit','execution.json','doctor.json','tool.log','tool_path.txt','receipt.txt','outputs/netlist.v','outputs/constraints.sdc','reports/area.rpt','reports/timing.rpt','reports/check_design.rpt','reports/constraints.rpt'}
    with zipfile.ZipFile(str(work/'console-return.zip'),'x',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(allowed):
            p=work/name
            if p.is_file() and not p.is_symlink():
                if p.stat().st_size>16*1024**2:raise ValueError('Oversized return retained on school host')
                z.write(str(p),name)
    save(work/'console-return.json',dict(key=key,archive_sha256=sha(work/'console-return.zip'),manifest_sha256=sha(root/'console-manifest.json')))
    try:ship(work,share)
    except (OSError,ValueError):print('Return retained; retry transfer only: '+ship_command(root,share))
    print(json.dumps(result));return 0 if result['status'] in ('FIXED_TEST_PASS','COMPLETED_REVIEW_REQUIRED') else 1

def ship_command(root,share):
    return ' '.join(shlex.quote(str(arg)) for arg in ('python3',root/'console_school_runner_v3.py','ship',share))

if __name__=='__main__':sys.exit(main())
