#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-fe9ee736d64940a5.zip"
timeout 60s cp -- "$share/console-fe9ee736d64940a5.zip" "$archive"
printf "%s  %s\n" "9732d43da0f1086eaaec532c12ec9fc0ca0b819eba7dc0349912623391b723a1" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="9732d43da0f1086eaaec532c12ec9fc0ca0b819eba7dc0349912623391b723a1":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"9732d43da0f1086eaaec532c12ec9fc0ca0b819eba7dc0349912623391b723a1")
PY
