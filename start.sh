#!/bin/bash
set -eu
here="$(cd -- "$(dirname -- "$0")" && pwd)"
dst="$HOME/xzy01-sampling-school34-package-v2"
state="$HOME/xzy01-sampling-school34-v2"
if [ -e "$state" ]; then
  echo "STOP: existing diagnostic state; do not rerun or remove reservations."
  exit 2
fi
if [ -e "$dst" ]; then
  echo "STOP: package directory already exists; inspect before proceeding."
  exit 2
fi
printf '%s  %s\n' 'f908f35c159756ac2c782919fdb3ab23fe2a0ff9b44fb82ae6e777e5d1ef9f7c' "$here/sampling-school34-v2.zip" | sha256sum -c -
mkdir "$dst"
cp "$here/sampling-school34-v2.zip" "$dst/package.zip"
printf '%s  %s\n' 'f908f35c159756ac2c782919fdb3ab23fe2a0ff9b44fb82ae6e777e5d1ef9f7c' "$dst/package.zip" | sha256sum -c -
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
