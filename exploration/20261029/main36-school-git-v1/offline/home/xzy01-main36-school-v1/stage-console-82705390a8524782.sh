#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-82705390a8524782.zip"
timeout 60s cp -- "$share/console-82705390a8524782.zip" "$archive"
printf "%s  %s\n" "0e852a2d442bbffc6bb6a77d080c63b567b8eb31369af9e2d97500b369199748" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="0e852a2d442bbffc6bb6a77d080c63b567b8eb31369af9e2d97500b369199748":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"0e852a2d442bbffc6bb6a77d080c63b567b8eb31369af9e2d97500b369199748")
PY
