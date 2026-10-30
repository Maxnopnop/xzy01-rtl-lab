#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-e7e2c518f1d04336.zip"
timeout 60s cp -- "$share/console-e7e2c518f1d04336.zip" "$archive"
printf "%s  %s\n" "c85e33f121f1dcbb95fec0bee3dfef98d830c27bc06097e00189fa01f1c5d8a4" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="c85e33f121f1dcbb95fec0bee3dfef98d830c27bc06097e00189fa01f1c5d8a4":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"c85e33f121f1dcbb95fec0bee3dfef98d830c27bc06097e00189fa01f1c5d8a4")
PY
