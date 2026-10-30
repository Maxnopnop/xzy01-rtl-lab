"""Python 3.6+ single manual DC netlist/Xcelium verification; no synthesis."""
import argparse,datetime,hashlib,json,os,re,shutil,signal,subprocess,sys,time,zipfile
from pathlib import Path

KEY='next96-dc-slot025-xcelium-v1'
SETUP='/usr/eelocal/cadence/xcelium2303hf/.cshrc'
MODEL='/staff/ee/dept/public/course_PDK/nangate/freepdk-45nm/lib/NangateOpenCellLibrary_PDKv1_3_v2010_12/Front_End/Verilog/NangateOpenCellLibrary.v'
MODEL_HASH='7b80af03f2ed72d40f014b836b13526aff3f64105415587c74f2260588b74363'
INPUTS={'school_sim.py','manifest.json','testbench.sv','reference.sv','netlist.v'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def verify(root):
    lock=read(root/'payload-lock.json')
    if set(lock)!=INPUTS:raise ValueError('Unexpected inputs')
    for name,h in lock.items():
        if sha(root/name)!=h:raise ValueError('Input changed: '+name)
    m=read(root/'manifest.json')
    if m['key']!=KEY:raise ValueError('Wrong experiment key')
    return m
def verdict(text,code):
    match=re.findall(r'^Mismatches: (\d+) in (\d+) samples$', '\n'.join(text.splitlines()),re.M)
    if code!=0:return dict(status='TOOL_ERROR')
    if len(match)!=1 or 'TIMEOUT' in text.upper():return dict(status='INVALID_OR_TIMEOUT_RECEIPT')
    n,t=map(int,match[0])
    return dict(status=('FIXED_TEST_PASS' if n==0 else 'FUNCTION_FAIL') if t==213 else 'CHECK_COUNT_DIFFERENT',mismatches=n,samples=t)
def reserve(path):path.mkdir(parents=True,exist_ok=False)
def bounded(argv,work,seconds=600):
    start=time.monotonic(); status='EXITED'
    with (work/'launcher.log').open('wb') as log:
        p=subprocess.Popen(argv,cwd=str(work),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while p.poll() is None:
                paths=[q for q in work.rglob('*') if q.is_file() and not q.is_symlink()]
                sizes=[q.stat().st_size for q in paths]
                if time.monotonic()-start>seconds:status='TIMEOUT'
                elif sum(sizes)>128*1024**2 or any(q.stat().st_size>16*1024**2 for q in paths if q.suffix=='.log'):status='RESOURCE_LIMIT'
                if status!='EXITED':os.killpg(p.pid,signal.SIGKILL);p.wait();break
                time.sleep(.25)
        except BaseException:
            if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
            raise
    return dict(status=status,returncode=p.returncode,elapsed_seconds=round(time.monotonic()-start,3),command=argv)
def collect(work,destination):
    allowed=INPUTS|{'payload-lock.json','run.csh','run.tcl','execution.json','result.json','tool_version.log','launcher.log','xrun.log','simulate.exit'}
    archive=work/('return-'+KEY+'.zip')
    with zipfile.ZipFile(str(archive),'x',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(allowed):
            p=work/name
            if p.is_file() and not p.is_symlink():
                if p.stat().st_size>16*1024**2:raise ValueError('Oversize return')
                z.write(str(p),name)
    side=work/('return-'+KEY+'.json')
    save(side,dict(kind='next96_dc_gatesim',key=KEY,archive=archive.name,archive_sha256=sha(archive),school_work=str(work)))
    ship(work,destination)
def ship(work,destination):
    side=work/('return-'+KEY+'.json');meta=read(side)
    if meta['archive']!='return-'+KEY+'.zip':raise ValueError('Invalid archive')
    archive=work/meta['archive']
    if sha(archive)!=meta['archive_sha256']:raise ValueError('Archive changed')
    try:
        for p in (archive,side):
            dest=destination/p.name
            if dest.exists():
                if sha(dest)!=sha(p):raise ValueError('Different existing return')
            else:
                with dest.open('xb') as f:f.write(p.read_bytes())
            if sha(dest)!=sha(p):raise ValueError('Transfer incomplete')
        print('RETURN COPIED: '+str(destination/archive.name),flush=True)
    except (OSError,ValueError) as e:
        print('RETURN RETAINED: '+str(archive)+'; '+str(e),flush=True)
        print('Transfer only: python3 '+str(work/'school_sim.py')+' ship --return-dir '+str(destination),flush=True)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['run','ship']);parser.add_argument('--return-dir',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parent;destination=Path(args.return_dir)
    work=Path.home()/'xzy01-next96-checks'/KEY
    if args.action=='ship':ship(work,destination);return 0
    m=verify(root)
    if os.name!='posix':raise ValueError('Run on school Linux only')
    if not Path(SETUP).is_file() or not shutil.which('tcsh'):raise ValueError('Xcelium setup/tcsh unavailable')
    if sha(MODEL)!=MODEL_HASH:raise ValueError('Model hash differs; no simulation started')
    if sha(Path.home()/'xzy01-next96-q38Nji/package/outputs/netlist.v')!=m['netlist_sha256']:raise ValueError('School DC netlist changed')
    reserve(work)
    for name in INPUTS|{'payload-lock.json'}:shutil.copyfile(str(root/name),str(work/name))
    record=dict(key=KEY,host=os.uname().nodename,started=datetime.datetime.utcnow().isoformat()+'Z',status='RESERVED',model_path=MODEL,model_sha256=sha(MODEL),setup_sha256=sha(SETUP),payload_lock_sha256=sha(work/'payload-lock.json'),netlist_sha256=sha(work/'netlist.v'),functional_defines=['TETRAMAX'],no_sdf=True)
    save(work/'execution.json',record)
    (work/'run.tcl').write_text('run\nexit\n')
    script='''#!/bin/tcsh -f
source "SETUP_PATH"
if ($status != 0) exit 90
rehash
xrun -version >& tool_version.log
if ($status != 0) exit 91
xrun -64bit -sv +define+TETRAMAX -nospecify -top tb testbench.sv reference.sv netlist.v -v "MODEL_PATH" +incdir+"MODEL_PARENT" -input run.tcl -l xrun.log
set sim_rc = $status
echo $sim_rc > simulate.exit
exit $sim_rc
'''.replace('SETUP_PATH',SETUP).replace('MODEL_PATH',MODEL).replace('MODEL_PARENT',str(Path(MODEL).parent))
    (work/'run.csh').write_text(script)
    print('ONE DC NETLIST / XCELIUM; WORK: '+str(work),flush=True)
    try:
        record.update(bounded(['tcsh','-f',str(work/'run.csh')],work))
        log=(work/'xrun.log').read_text(errors='replace') if (work/'xrun.log').exists() else ''
        result=verdict(log,record['returncode']) if record['status']=='EXITED' else dict(status=record['status'])
        verify(work)
        if sha(MODEL)!=MODEL_HASH:raise ValueError('Library changed during simulation')
    except (OSError,ValueError) as e:
        result=dict(status='ENVIRONMENT_OR_EVIDENCE_ERROR',error=str(e));record['status']=result['status']
    record['finished']=datetime.datetime.utcnow().isoformat()+'Z'
    save(work/'execution.json',record);save(work/'result.json',result)
    print(json.dumps(result),flush=True);collect(work,destination)
    return 0 if result['status']=='FIXED_TEST_PASS' else 1
if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError) as e:print('STOP: '+str(e));sys.exit(2)
