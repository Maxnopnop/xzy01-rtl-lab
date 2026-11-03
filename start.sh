#!/bin/bash
set -eu
here="$(cd -- "$(dirname -- "$0")" && pwd)"
dst="$HOME/xzy01-sampling-school34-package-v1"
state="$HOME/xzy01-sampling-school34-v1"
if [ -e "$state" ]; then
  echo "STOP: existing diagnostic state; do not rerun or remove reservations."
  exit 2
fi
if [ -e "$dst" ]; then
  echo "STOP: package directory already exists; inspect before proceeding."
  exit 2
fi
printf '%s  %s\n' 'e9ccff6766790e83629880fb640334e71f1fc45c7f34d632311c87dd251ab062' "$here/sampling-school34-v1.zip" | sha256sum -c -
mkdir "$dst"
cp "$here/sampling-school34-v1.zip" "$dst/package.zip"
printf '%s  %s\n' 'e9ccff6766790e83629880fb640334e71f1fc45c7f34d632311c87dd251ab062' "$dst/package.zip" | sha256sum -c -
python3 -m zipfile -e "$dst/package.zip" "$dst"
python3 -B "$dst/run.py" check
set +e
python3 -B "$dst/run.py" run
rc=$?
set -e
echo "Batch exit=$rc. Do not rerun failed jobs or remove STOP/state."
echo "Local evidence: $state"
echo "Local exports: $state/exports"
exit "$rc"
