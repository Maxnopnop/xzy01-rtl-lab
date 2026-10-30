"""R6 v1 append-only bytes + durable exit proof. Direct child cleanup only."""
import contextlib, ctypes, hashlib, json, os, subprocess, threading, time, uuid
from pathlib import Path

def digest(data): return hashlib.sha256(data).hexdigest()
def utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
def atomic(p, obj):
    p=Path(p);tmp=p.with_name(p.name+'.tmp')
    with tmp.open('w',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def durable_bytes(p,data):
    with Path(p).open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())

def identity(pid):
    if os.name!='nt':
        try:return Path('/proc',str(pid),'stat').read_text().split()[21]
        except OSError:return None
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.restype=ctypes.c_void_p
    k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
    k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.c_void_p]*4
    k.CloseHandle.argtypes=[ctypes.c_void_p]
    k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
    h=k.OpenProcess(0x1000|0x100000,False,pid)
    if not h:return None
    if k.WaitForSingleObject(h,0)==0:k.CloseHandle(h);return None
    times=[ctypes.c_ulonglong() for _ in range(4)]
    ok=k.GetProcessTimes(h,*[ctypes.byref(t) for t in times]);k.CloseHandle(h)
    return str(times[0].value) if ok else None

@contextlib.contextmanager
def lock(folder):
    p=Path(folder)/'writer.lock';f=p.open('a+b')
    if p.stat().st_size==0:f.write(b'0');f.flush()
    f.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        f.close();raise RuntimeError('ACTIVE_WRITER_LOCK') from None
    try:yield
    finally:
        f.seek(0)
        if os.name=='nt':msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
        else:fcntl.flock(f,fcntl.LOCK_UN)
        f.close()

def capture(command, folder, prompt, model, timeout=180, output_limit=2*1024*1024,
            env=None, cwd=None, nonce=None, after_exit=None, context=None):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    with lock(folder):
        if (folder/'reservation.json').exists():raise RuntimeError('NO_RESEND_RESERVED')
        nonce=nonce or uuid.uuid4().hex
        request=dict(nonce=nonce,model=model,prompt_bytes=len(prompt),prompt_sha256=digest(prompt),
                     timeout=timeout,output_limit=output_limit,command=command,created_utc=utc(),context=context or {})
        atomic(folder/'request.json',request)
        durable_bytes(folder/'prompt.bin',prompt)
        atomic(folder/'reservation.json',dict(utc=utc(),reserved_calls=1,request_sha256=digest((folder/'request.json').read_bytes())))
        # A reservation remains unknown if process creation/start proof is lost.
        proc=subprocess.Popen(command,cwd=cwd or folder,env=env,stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        start=dict(utc=utc(),pid=proc.pid,identity=identity(proc.pid),writer_pid=os.getpid(),
                   writer_identity=identity(os.getpid()),nonce=nonce,request_sha256=digest((folder/'request.json').read_bytes()))
        atomic(folder/'process-start.json',start)
        stop=threading.Event();counts={'stdout':0,'stderr':0};errors=[];journal_lock=threading.Lock()
        journal=(folder/'chunks.jsonl').open('ab',buffering=0)
        def drain(name,pipe):
            try:
                with (folder/(name+'.bin')).open('xb',buffering=0) as f:
                    while True:
                        chunk=os.read(pipe.fileno(),4096)
                        if not chunk:break
                        f.write(chunk);os.fsync(f.fileno());counts[name]+=len(chunk)
                        with journal_lock:
                            journal.write((json.dumps(dict(utc=utc(),stream=name,end=counts[name],bytes=len(chunk),sha256=digest(chunk),nonce=nonce))+'\n').encode());os.fsync(journal.fileno())
                        if sum(counts.values())>output_limit:stop.set()
            except BaseException as e:errors.append(type(e).__name__);stop.set()
        ts=[threading.Thread(target=drain,args=(n,pipe),daemon=True) for n,pipe in [('stdout',proc.stdout),('stderr',proc.stderr)]]
        for t in ts:t.start()
        def feed():
            try:proc.stdin.write(prompt);proc.stdin.close()
            except (BrokenPipeError,OSError):pass
        threading.Thread(target=feed,daemon=True).start()
        begin=time.monotonic();reason=None
        try:
            while proc.poll() is None:
                if stop.is_set():reason='OUTPUT_LIMIT' if sum(counts.values())>output_limit else 'READER_ERROR';break
                if time.monotonic()-begin>timeout:reason='TIMEOUT';break
                time.sleep(.01)
            if reason:
                # Only the retained Popen handle belonging to this call is terminated.
                proc.kill()
            code=proc.wait(timeout=5)
            for t in ts:t.join(timeout=2)
            complete=all(not t.is_alive() for t in ts)
            if sum(counts.values())>output_limit:reason='OUTPUT_LIMIT'
            proof=dict(utc=utc(),pid=proc.pid,identity=start['identity'],nonce=nonce,
                       request_sha256=start['request_sha256'],returncode=code,reason=reason,
                       elapsed_seconds=time.monotonic()-begin,streams_closed=complete,
                       reader_errors=errors,counts=counts.copy(),descendant_cleanup='UNVERIFIED',
                       sha256={n:digest((folder/(n+'.bin')).read_bytes()) for n in counts})
            atomic(folder/'exit-proof.json',proof)
            if after_exit:after_exit(folder)
            result=recover(folder,locked=True)
            atomic(folder/'capture-summary.json',result)
            return result
        finally:journal.close()

def recover(folder,locked=False):
    try:return _recover(folder,locked)
    except (OSError,ValueError,KeyError,TypeError) as e:
        return dict(status='UNKNOWN_INTERRUPTED',usage=None,source='READ_ONLY_SAVED_EVIDENCE',boundary='MALFORMED_OR_MISSING_EVIDENCE',error_type=type(e).__name__)

def _recover(folder,locked=False):
    folder=Path(folder)
    if not locked:
        if not (folder/'writer.lock').exists():
            return dict(status='UNKNOWN_INTERRUPTED',usage=None,source='READ_ONLY_SAVED_EVIDENCE',reserved_calls=int((folder/'reservation.json').exists()),boundary='RESERVED_NO_START_PROOF' if not (folder/'process-start.json').exists() else 'NO_LOCK_PROOF')
        with lock(folder):return recover(folder,True)
    result=dict(status='UNKNOWN_INTERRUPTED',usage=None,source='READ_ONLY_SAVED_EVIDENCE',reserved_calls=int((folder/'reservation.json').exists()))
    if not (folder/'reservation.json').exists():return result|dict(status='NOT_RESERVED')
    req=read(folder/'request.json');res=read(folder/'reservation.json')
    rh=digest((folder/'request.json').read_bytes())
    if rh!=res['request_sha256'] or digest((folder/'prompt.bin').read_bytes())!=req['prompt_sha256']:return result|dict(boundary='REQUEST_MISMATCH')
    if not (folder/'process-start.json').exists():return result|dict(boundary='RESERVED_NO_START_PROOF')
    start=read(folder/'process-start.json')
    if identity(start['pid'])==start['identity'] and start['identity'] is not None:
        return result|dict(status='ACTIVE_CHILD',boundary='PROCESS_IDENTITY_MATCH')
    if not (folder/'exit-proof.json').exists():return result|dict(boundary='PARTIAL_OR_EXIT_UNOBSERVED')
    proof=read(folder/'exit-proof.json')
    if any(proof[k]!=start[k] for k in ['pid','identity','nonce','request_sha256']) or start['request_sha256']!=rh:return result|dict(boundary='EXIT_BINDING_MISMATCH')
    for n in ['stdout','stderr']:
        b=(folder/(n+'.bin')).read_bytes()
        if len(b)!=proof['counts'][n] or digest(b)!=proof['sha256'][n]:return result|dict(boundary='STREAM_MISMATCH')
    offsets={'stdout':0,'stderr':0}
    chunks=[json.loads(line) for line in (folder/'chunks.jsonl').read_text().splitlines()]
    for c in chunks:
        name=c['stream'];begin=offsets[name];end=c['end'];data=(folder/(name+'.bin')).read_bytes()[begin:end]
        if c['nonce']!=req['nonce'] or end-begin!=c['bytes'] or digest(data)!=c['sha256']:return result|dict(boundary='CHUNK_BINDING_MISMATCH')
        offsets[name]=end
    if offsets!=proof['counts']:return result|dict(boundary='CHUNK_COVERAGE_MISMATCH')
    if not proof['streams_closed'] or proof['reader_errors']:return result|dict(boundary='UNCLOSED_STREAM')
    if proof['reason'] or proof['returncode']!=0:return result|dict(boundary=proof['reason'] or 'NONZERO_EXIT',exit=proof)
    try:events=[json.loads(x) for x in (folder/'stdout.bin').read_bytes().decode('utf-8').splitlines() if x.strip()]
    except (ValueError,UnicodeError):return result|dict(boundary='INVALID_OR_PARTIAL_EVENTS')
    threads=[e for e in events if e.get('type')=='thread.started'];done=[e for e in events if e.get('type')=='turn.completed'];begins=[e for e in events if e.get('type')=='turn.started']
    if len(threads)!=1 or len(begins)!=1 or len(done)!=1 or events[-1].get('type')!='turn.completed' or events[0].get('type')!='thread.started' or any(e.get('type') in ['error','turn.failed'] for e in events):return result|dict(boundary='NONCLEAN_TURN')
    items=[e['item'] for e in events if e.get('type')=='item.completed']
    if any(e.get('item',{}).get('type') not in ['agent_message','reasoning'] for e in events if e.get('type','').startswith('item.')):return result|dict(boundary='TOOL_EVENT')
    messages=[i['text'] for i in items if i.get('type')=='agent_message' and isinstance(i.get('text'),str)]
    u=done[0].get('usage')
    if len(messages)!=1 or not messages[0].strip() or not isinstance(u,dict) or any(type(u.get(k))!=int or u[k]<0 for k in ['input_tokens','output_tokens','cached_input_tokens']):return result|dict(boundary='MISSING_RESPONSE_OR_USAGE')
    if u['cached_input_tokens']>u['input_tokens']:return result|dict(boundary='USAGE_INCONSISTENT')
    final=req.get('context',{}).get('final_output_name')
    if final and (not (folder/final).is_file() or (folder/final).read_bytes()!=messages[0].encode()):return result|dict(boundary='FINAL_FILE_MISMATCH')
    return result|dict(status='GENERATED',response=messages[0],response_sha256=digest(messages[0].encode()),
                       usage=u,thread_id=threads[0]['thread_id'],exit=proof,
                       reconstructed_without_summary=not (folder/'capture-summary.json').exists())
