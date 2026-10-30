#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-0358b837b0844136.zip"
timeout 60s cp -- "$share/console-0358b837b0844136.zip" "$archive"
printf "%s  %s\n" "0d5fe71b97ab3f23eaabc3af9da48abce882ccb13375f5a8aaa8c652f55ff1c3" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="0d5fe71b97ab3f23eaabc3af9da48abce882ccb13375f5a8aaa8c652f55ff1c3":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"0d5fe71b97ab3f23eaabc3af9da48abce882ccb13375f5a8aaa8c652f55ff1c3")
PY
