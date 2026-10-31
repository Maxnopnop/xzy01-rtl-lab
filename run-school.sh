#!/usr/bin/env bash
set -u
cd -- "$(dirname -- "$0")"
export PYTHONDONTWRITEBYTECODE=1
python3 runner.py check || exit $?
python3 -u runner.py run-all
rc=$?
python3 runner.py export
echo "Batch exit=$rc. Do not rerun failed jobs or remove STOP/locks."
exit "$rc"
