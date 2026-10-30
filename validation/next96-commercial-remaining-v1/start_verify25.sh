#!/usr/bin/env bash
set -eu
case "${1:-}" in
  xcelium-rtl) archive="next96-rtl-slot025-xcelium-v1.zip"; digest="4de473e686b3422b8c9d988fdf9cb6959198208090de1ba705ef79b231c0ae93" ;;
  vcs-rtl) archive="next96-rtl-slot025-vcs-v1.zip"; digest="0620f068706255284f02a41293a9b774525dc20977913339b3b694e36168a1b0" ;;
  vcs-dc) archive="next96-dc-slot025-vcs-v1.zip"; digest="b61b37259eea231e66ab777ea298299ad71a64c63f525309e095e7a4991cc62b" ;;
  *) echo 'Choose ONE: xcelium-rtl | vcs-rtl | vcs-dc'; exit 2 ;;
esac
share_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$share_dir/$archive" "$digest" "$share_dir" <<'PY_BOOT'
import hashlib,io,os,sys,tempfile,zipfile
from pathlib import Path
blob=Path(sys.argv[1]).read_bytes()
if hashlib.sha256(blob).hexdigest()!=sys.argv[2]:raise SystemExit('STOP: ZIP hash mismatch')
work=Path(tempfile.mkdtemp(prefix='next96-single-payload-',dir=str(Path.home())))
common={'school_sim.py','manifest.json','testbench.sv','reference.sv','payload-lock.json'}
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    names=set(z.namelist())
    if names not in (common|{'dut.sv'},common|{'netlist.v'}) or len(z.namelist())!=6 or z.testzip() is not None:raise SystemExit('STOP: ZIP members invalid')
    for name in sorted(names):(work/name).write_bytes(z.read(name))
os.execv(sys.executable,[sys.executable,str(work/'school_sim.py'),'run','--return-dir',sys.argv[3]])
PY_BOOT
