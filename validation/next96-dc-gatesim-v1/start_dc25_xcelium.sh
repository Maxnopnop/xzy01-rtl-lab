#!/usr/bin/env bash
set -eu
share_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$share_dir/next96-dc-slot025-xcelium-v1.zip" "fed1ea064516d06a18dc57a755a3ef767637927ff2661623d327b33205d3e7ca" "$share_dir" <<'PY_BOOT'
import hashlib,io,os,sys,tempfile,zipfile
from pathlib import Path
blob=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(blob).hexdigest()!=sys.argv[2]:raise SystemExit('STOP: ZIP hash mismatch')
allowed={'school_sim.py','manifest.json','testbench.sv','reference.sv','netlist.v','payload-lock.json'}
work=Path(tempfile.mkdtemp(prefix='next96-gate-payload-',dir=str(Path.home())))
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    if set(z.namelist())!=allowed or len(z.namelist())!=len(allowed) or z.testzip() is not None:raise SystemExit('STOP: Unexpected ZIP')
    for name in sorted(allowed):(work/name).write_bytes(z.read(name))
os.execv(sys.executable,[sys.executable,str(work/'school_sim.py'),'run','--return-dir',sys.argv[3]])
PY_BOOT
