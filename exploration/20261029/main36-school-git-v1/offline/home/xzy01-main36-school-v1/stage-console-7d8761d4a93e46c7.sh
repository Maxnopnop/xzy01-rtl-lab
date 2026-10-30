#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-7d8761d4a93e46c7.zip"
timeout 60s cp -- "$share/console-7d8761d4a93e46c7.zip" "$archive"
printf "%s  %s\n" "3b62a1004dec74a4705e50e47ad4d1904bea91805bec4fc6bab236433ad1e341" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="3b62a1004dec74a4705e50e47ad4d1904bea91805bec4fc6bab236433ad1e341":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"3b62a1004dec74a4705e50e47ad4d1904bea91805bec4fc6bab236433ad1e341")
PY
