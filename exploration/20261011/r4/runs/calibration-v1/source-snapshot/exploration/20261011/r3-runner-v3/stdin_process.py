"""Versioned process adapter: exact UTF-8 file on stdin, existing time/output/tree bounds."""
import os,subprocess,time,threading
from pathlib import Path
from rtl_lab import clean_env,kill_tree,MAX_LOG

def run_process_stdin(command, cwd, timeout, env, stdin_path):
    """Bound wall time and captured output; reap the process tree on timeout."""
    start = time.monotonic()
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    with Path(stdin_path).open('rb') as source:
        proc = subprocess.Popen(command, cwd=cwd, env=env or clean_env(),
                                stdin=source, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kwargs)
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    overflow = threading.Event()

    def drain(stream, name):
        while True:
            piece = stream.read(8192)
            if not piece:
                break
            room = MAX_LOG - len(chunks[name])
            chunks[name].extend(piece[:max(0, room)])
            if len(piece) > room:
                overflow.set()
        stream.close()

    readers = [threading.Thread(target=drain, args=(getattr(proc, name), name), daemon=True)
               for name in chunks]
    for reader in readers:
        reader.start()
    timed_out = False
    killed = False
    try:
        while proc.poll() is None:
            if time.monotonic() - start > timeout or overflow.is_set():
                timed_out = time.monotonic() - start > timeout
                kill_tree(proc)
                killed = True
                break
            time.sleep(0.02)
    except BaseException:
        kill_tree(proc)
        raise
    finally:
        for reader in readers:
            reader.join(timeout=5)
    return {"command": [str(x) for x in command], "returncode": proc.returncode,
            "elapsed_seconds": round(time.monotonic() - start, 4), "timeout": timed_out,
            "output_limit": overflow.is_set(), "killed": killed, "pid": proc.pid,
            **{key: bytes(value).decode("utf-8", errors="replace") for key, value in chunks.items()}}

