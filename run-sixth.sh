#!/usr/bin/env bash
set -u
cd -- "$(dirname -- "$0")"
export PYTHONDONTWRITEBYTECODE=1
python3 single.py check || exit $?
python3 -u single.py run
rc=$?
python3 single.py ship
echo "Separate sixth attempt exit=$rc; old batch results unchanged."
exit "$rc"
