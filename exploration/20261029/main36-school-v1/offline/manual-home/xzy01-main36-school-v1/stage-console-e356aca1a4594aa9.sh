#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-e356aca1a4594aa9.zip"
timeout 60s cp -- "$share/console-e356aca1a4594aa9.zip" "$archive"
printf "%s  %s\n" "d3fb0eaf7fb599c01fa9527269113a19c9410ab2d2e84ae287bbc0b1e0e43153" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="d3fb0eaf7fb599c01fa9527269113a19c9410ab2d2e84ae287bbc0b1e0e43153":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"d3fb0eaf7fb599c01fa9527269113a19c9410ab2d2e84ae287bbc0b1e0e43153")
PY
