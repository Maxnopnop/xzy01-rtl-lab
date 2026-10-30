#!/usr/bin/env bash
set -eu
share_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$share_dir/xzy01-gate-diag-v2.zip" "ce508dbff84e8411f8ef473ef932aff88724d8b1eac42d35520741651aa7218b" "dc" "$share_dir" <<'PY_GATE_BOOT'
import hashlib,os,sys,tempfile,zipfile,io
from pathlib import Path
blob=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(blob).hexdigest()!=sys.argv[2]:
    raise SystemExit('STOP: gate-check bundle hash mismatch')
work=Path(tempfile.mkdtemp(prefix='xzy01-gate-payload-',dir=str(Path.home())))
allowed={'ece_gate_check.py','testbench.sv','rt_sequence.hex','manifest.json','payload-lock.json'}
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    if set(z.namelist())!=allowed or len(z.namelist())!=len(allowed) or z.testzip() is not None:
        raise SystemExit('STOP: unexpected payload members or bad CRC')
    for name in sorted(allowed):
        (work/name).write_bytes(z.read(name))
os.execv(sys.executable,[sys.executable,str(work/'ece_gate_check.py'),sys.argv[3],'--return-dir',sys.argv[4],'--diagnostic'])
PY_GATE_BOOT
