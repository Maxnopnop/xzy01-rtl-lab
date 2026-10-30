#!/usr/bin/env bash
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
work="$HOME/xzy01-console-transfer-v1"
mkdir -p "$work"
if [ ! -f "$work/verify25-transfer-v1.zip" ]; then
  timeout 60s cp "$base/verify25-transfer-v1.zip" "$work/verify25-transfer-v1.zip"
fi
cd "$work"
printf '%s  %s
' '238288af017b6d7a5e405e60873c17d2c27c56f38d055e932b233536e8f16d91' verify25-transfer-v1.zip | sha256sum -c -
python3 - <<'PY'
import hashlib,json,zipfile
from pathlib import Path
with zipfile.ZipFile('verify25-transfer-v1.zip') as z:
    names=z.namelist()
    if len(names)!=51 or len(set(names))!=51:raise ValueError('Archive members')
    for n in names:
        p=Path(n)
        if p.is_absolute() or '..' in p.parts or ':' in n or '\\' in n:raise ValueError('Unsafe name')
        raw=z.read(n)
        if p.exists():
            if p.read_bytes()!=raw:raise ValueError('Existing staged file changed: '+n)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(raw)
    for n,h in json.loads(z.read('transfer-lock.json').decode()).items():
        if hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h:raise ValueError('Input hash: '+n)
print('STAGED: 48 original frozen files unchanged; no EDA started')
PY
exec python3 "$work/run-local.py" check
