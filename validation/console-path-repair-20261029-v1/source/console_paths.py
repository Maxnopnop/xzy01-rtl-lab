"""Exact-target writable probes and sanitized post-send storage failure evidence."""
import hashlib
import os
from pathlib import Path

LIMIT=240  # Conservative Windows/tool budget, independent of registry long-path policy.

def error_record(exc,stage):
    # Never include exception messages, paths, response text, or credentials.
    return dict(stage=stage,error_type=type(exc).__name__,errno=getattr(exc,'errno',None),winerror=getattr(exc,'winerror',None))

def probe(path):
    path=Path(path).resolve()
    if len(str(path))>=LIMIT:raise OSError(36,'Path exceeds conservative preflight budget')
    path.parent.mkdir(parents=True,exist_ok=True)
    payload=b'OFFLINE_WRITABILITY_PROBE\n'
    with path.open('xb') as f:
        f.write(payload);f.flush();os.fsync(f.fileno())
    if path.read_bytes()!=payload:raise OSError('Probe readback mismatch')
    path.unlink()

def preflight(folder,other_paths,assets=()):
    """Touch every currently emitted file path, including deeper local replay outputs.

    No tools run. This cannot guarantee future disk capacity/permissions, hence
    post-send fallback remains mandatory. Remove only empty directories we made.
    """
    folder=Path(folder)
    names=['request.json','reservation.json','attempt.json','transport-response.json','model-output.txt','dut.sv','testbench.sv','reference.sv','result.json']
    local=['dut.sv','testbench.sv','reference.sv','input-lock.json','compile.json','simulate.json','synthesis.json','synthesis.ys','sim.vvp','netlist.json','netlist.v','result.json']
    targets=[folder/n for n in names]+[folder/'local'/n for n in local]
    targets += [folder/n for n in assets]+[folder/'local'/n for n in assets]
    targets += list(other_paths)
    if len(set(targets))!=len(targets):raise ValueError('Asset collides with generated evidence')
    created=set()
    try:
        for p in targets:
            q=p.parent
            while not q.exists():created.add(q);q=q.parent
            probe(p)
    finally:
        for p in sorted(created,key=lambda x:len(x.parts),reverse=True):
            try:p.rmdir()
            except OSError:pass
    return dict(paths=[str(p) for p in targets],max_length=max(len(str(p)) for p in targets),tool_calls=0)
