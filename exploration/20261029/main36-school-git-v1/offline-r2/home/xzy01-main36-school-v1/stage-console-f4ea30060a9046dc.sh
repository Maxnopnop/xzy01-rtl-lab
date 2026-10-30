#!/usr/bin/env bash
set -eu
share=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/xzy01-console-v3/archives"
archive="$HOME/xzy01-console-v3/archives/console-f4ea30060a9046dc.zip"
timeout 60s cp -- "$share/console-f4ea30060a9046dc.zip" "$archive"
printf "%s  %s\n" "b25272a2c0f5b10a076fc76320ddf5ad3491fcfa810539b594b33363b1dd69a1" "$archive" | sha256sum -c -
python3 - "$archive" <<'PY'
import hashlib,sys,zipfile
from pathlib import Path
p=Path(sys.argv[1])
if hashlib.sha256(p.read_bytes()).hexdigest()!="b25272a2c0f5b10a076fc76320ddf5ad3491fcfa810539b594b33363b1dd69a1":raise SystemExit("ZIP changed")
with zipfile.ZipFile(str(p)) as z: code=z.read("console_stage_v3.py")
if hashlib.sha256(code).hexdigest()!="07b6b0aed5cdca1b33d8eafc5952ce537bdf175022b7cc1553c3a4daad5120ea":raise SystemExit("Stage code changed")
ns={"__name__":"verified_stage"};exec(compile(code,"verified-stage","exec"),ns)
ns["stage"](p,"b25272a2c0f5b10a076fc76320ddf5ad3491fcfa810539b594b33363b1dd69a1")
PY
