#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-959f371d2af442fe.zip"
timeout 60s cp -- "$share/console-959f371d2af442fe.zip" "$archive"
printf "%s  %s\n" "83dc94787f7b99d9be5dd4c8b1f9c811669be6a4d68a1e0ad6d089a17aee66bf" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="83dc94787f7b99d9be5dd4c8b1f9c811669be6a4d68a1e0ad6d089a17aee66bf":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"83dc94787f7b99d9be5dd4c8b1f9c811669be6a4d68a1e0ad6d089a17aee66bf")
PY
