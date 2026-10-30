#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-4e319d9a0dbf41c1.zip"
timeout 60s cp -- "$share/console-4e319d9a0dbf41c1.zip" "$archive"
printf "%s  %s\n" "34a3884114d86172a6aef4200cdd797923476a6a1819da2b3f63624c6422c90f" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="34a3884114d86172a6aef4200cdd797923476a6a1819da2b3f63624c6422c90f":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"34a3884114d86172a6aef4200cdd797923476a6a1819da2b3f63624c6422c90f")
PY
