#!/bin/bash
# Run on the ECE desktop. Copies/unpacks one prepared ZIP and checks the environment only.
set -eu
transfer_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
archive=${1:-"$transfer_dir/ece-vcs-ready-20261008.zip"}
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' 'Python 3 is unavailable. Copy the ZIP to your home directory and use the manual tcsh fallback in the guide.'
    exit 2
fi
python3 - "$archive" <<'PY'
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
import shlex

archive = Path(sys.argv[1]).resolve()
expected = Path(str(archive) + '.sha256').read_text().strip().split()[0]
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise SystemExit('ZIP hash mismatch; nothing executed')
parent = Path.home() / 'xzy01-ece'
parent.mkdir(exist_ok=True)
target = Path(tempfile.mkdtemp(prefix='session_', dir=str(parent)))
local = target / archive.name
shutil.copyfile(str(archive), str(local))
with zipfile.ZipFile(str(local)) as z:
    seen = set()
    members = z.infolist()
    if len(members) > 5000 or sum(m.file_size for m in members) > 100 * 1024 * 1024:
        raise SystemExit('ZIP exceeds limits')
    for m in members:
        parts = PurePosixPath(m.filename).parts
        if not parts or parts[0] != archive.stem or '..' in parts or '\\' in m.filename or ':' in m.filename or m.filename in seen or stat.S_ISLNK(m.external_attr >> 16):
            raise SystemExit('Unsafe ZIP path')
        seen.add(m.filename)
    z.extractall(str(target))
root = target / archive.stem
print('Copied to school HOME: ' + str(root), flush=True)
code = subprocess.call([sys.executable, 'ece_desktop.py', 'doctor'], cwd=str(root))
if code:
    raise SystemExit(code)
meta = json.loads((root / 'package.json').read_text())['cases'][0]
print('\nEnvironment check only; no EDA simulation was started.')
print('After reviewing the doctor output, run ONE case manually:')
print('cd ' + shlex.quote(str(root)))
print('python3 ece_desktop.py run --case ' + shlex.quote(meta['job_id']))
PY
