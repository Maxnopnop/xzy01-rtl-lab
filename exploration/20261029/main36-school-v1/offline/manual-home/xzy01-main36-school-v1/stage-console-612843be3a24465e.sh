#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-612843be3a24465e.zip"
timeout 60s cp -- "$share/console-612843be3a24465e.zip" "$archive"
printf "%s  %s\n" "0d5d3dd5ad2bf13e63a726382a6b2e22b3f6bb8a218731f018a5ea04a56d37d5" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="0d5d3dd5ad2bf13e63a726382a6b2e22b3f6bb8a218731f018a5ea04a56d37d5":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"0d5d3dd5ad2bf13e63a726382a6b2e22b3f6bb8a218731f018a5ea04a56d37d5")
PY
