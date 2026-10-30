#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-dc8719ffdc484dfa.zip"
timeout 60s cp -- "$share/console-dc8719ffdc484dfa.zip" "$archive"
printf "%s  %s\n" "8c04237f62d511589722b9f0d07e0ec12c715b32428425bab952be337d0d155e" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="8c04237f62d511589722b9f0d07e0ec12c715b32428425bab952be337d0d155e":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"8c04237f62d511589722b9f0d07e0ec12c715b32428425bab952be337d0d155e")
PY
