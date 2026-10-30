"""Bounded real OS subprocess tests; all outputs are ARTIFICIAL, not LLM evidence."""
import hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path
import stream_process as s
BASE=Path(__file__).resolve().parent
RUN=BASE/'runs/process-v3'
assert not RUN.exists();RUN.mkdir(parents=True)
receipts=[]
(RUN/'source-snapshot').mkdir()
for filename in ['stream_process.py','mock_cli.py','record_worker.py']:
    (RUN/'source-snapshot'/filename).write_bytes((BASE/filename).read_bytes())
def waitfile(p):
    end=time.monotonic()+6
    while not p.exists():
        assert time.monotonic()<end,'Fixture readiness timeout'
        time.sleep(.02)
def record(name,result):receipts.append(dict(case=name,result=result))
try:
    for mode,boundary in [('clean',None),('nonzero','NONZERO_EXIT'),('hang','TIMEOUT'),('partial','TIMEOUT'),('limit','OUTPUT_LIMIT'),('tool','TOOL_EVENT'),('missingusage','MISSING_RESPONSE_OR_USAGE')]:
        p=RUN/mode;nonce=uuid.uuid4().hex;prompt=('MOCK transport 中文 '+nonce).encode()
        r=s.capture([sys.executable,str(BASE/'mock_cli.py'),mode,nonce],p,prompt,'ARTIFICIAL_NO_MODEL',timeout=.5,output_limit=4096,nonce=nonce)
        received=s.read(p/'received.json');assert received['bytes']==len(prompt) and received['sha256']==s.digest(prompt)
        if boundary:assert r['status']=='UNKNOWN_INTERRUPTED' and r['usage'] is None and r['boundary']==boundary,r
        else:assert r['status']=='GENERATED' and r['response']=='MOCK 中文 '+nonce
        before={str(x.relative_to(p)):s.digest(x.read_bytes()) for x in p.rglob('*') if x.is_file()}
        try:s.capture([sys.executable,'-c','raise AssertionError("must not launch")'],p,b'bad','ARTIFICIAL_NO_MODEL')
        except RuntimeError as e:assert str(e)=='NO_RESEND_RESERVED'
        else:raise AssertionError('Duplicate send permitted')
        assert before=={str(x.relative_to(p)):s.digest(x.read_bytes()) for x in p.rglob('*') if x.is_file()}
        record(mode,r)
    # Persist reservation without local start proof; never infer no provider usage.
    p=RUN/'reserved-only';p.mkdir();req=dict(prompt_sha256=s.digest(b'x'));s.atomic(p/'request.json',req);(p/'prompt.bin').write_bytes(b'x')
    s.atomic(p/'reservation.json',dict(request_sha256=s.digest((p/'request.json').read_bytes())))
    r=s.recover(p);assert r['boundary']=='RESERVED_NO_START_PROOF' and r['usage'] is None;record('reserved-only',r)
    for mode in ['partial','completed-hang','clean']:
        p=RUN/('writer-kill-'+mode);nonce=uuid.uuid4().hex
        writer=subprocess.Popen([sys.executable,str(BASE/'record_worker.py'),str(p),mode,nonce],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        waitfile(p/'process-start.json');start=s.read(p/'process-start.json')
        if mode=='clean':
            assert writer.wait(timeout=6)==91;assert not (p/'capture-summary.json').exists()
            r=s.recover(p);assert r['status']=='GENERATED' and r['reconstructed_without_summary'];record('completed-exit-before-summary',r)
            continue
        waitfile(p/'stdout.bin')
        end=time.monotonic()+4
        while (p/'stdout.bin').stat().st_size<100:
            assert time.monotonic()<end;time.sleep(.02)
        try:
            s.recover(p)
        except RuntimeError as e:assert str(e)=='ACTIVE_WRITER_LOCK'
        else:raise AssertionError('Live lock accepted')
        writer.kill();writer.wait(timeout=4)
        r=s.recover(p);assert r['status']=='ACTIVE_CHILD' and r['usage'] is None;record('writer-killed-child-alive-'+mode,r)
        # Scope: exact fixture child PID AND creation identity; no global cleanup.
        assert s.identity(start['pid'])==start['identity']
        if os.name=='nt':
            k=__import__('ctypes').WinDLL('kernel32');k.OpenProcess.restype=__import__('ctypes').c_void_p
            k.TerminateProcess.argtypes=[__import__('ctypes').c_void_p,__import__('ctypes').c_uint]
            k.CloseHandle.argtypes=[__import__('ctypes').c_void_p]
            h=k.OpenProcess(1,False,start['pid']);assert h;assert k.TerminateProcess(h,92);k.CloseHandle(h)
        else:os.kill(start['pid'],9)
        end=time.monotonic()+4
        while s.identity(start['pid']) is not None:assert time.monotonic()<end;time.sleep(.02)
        r=s.recover(p);assert r['status']=='UNKNOWN_INTERRUPTED' and r['usage'] is None;record('writer-killed-child-stopped-'+mode,r)
    # Same reserved 48-slot denominator remains despite offline interruption.
    assert len(receipts)==13
    s.atomic(RUN/'summary.json',dict(status='PASS',label='ARTIFICIAL_OFFLINE_OS_ACCEPTANCE',model_calls=0,cases=receipts,planned_research_denominator=48,descendant_cleanup='UNVERIFIED'))
except BaseException as e:
    s.atomic(RUN/'failure.json',dict(type=type(e).__name__,message=str(e),receipts=receipts));raise
finally:
    s.atomic(RUN/'evidence-lock.json',{str(p.relative_to(RUN)):s.digest(p.read_bytes()) for p in RUN.rglob('*') if p.is_file() and p.name!='evidence-lock.json'})
print('ARTIFICIAL PASS; 13 cases; model calls 0; descendant cleanup UNVERIFIED')
