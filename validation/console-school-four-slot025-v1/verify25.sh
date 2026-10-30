#!/usr/bin/env bash
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
action=${1:-check}
tool=${2:-}
if [ "$action" = check ]; then
  python3 "$base/check-all.py" "$base"
  exit $?
fi
case "$tool" in
  vcs) key=console-870895a9257949b6 ;;
  xcelium) key=console-c1078a5faa404f35 ;;
  dc) key=console-ced38ec605c34bdc ;;
  genus) key=console-39f67a9de4784541 ;;
  *) echo "Select ONE tool: vcs xcelium dc genus"; exit 2 ;;
esac
case "$action" in
  run) script=run-one.sh ;;
  ship) script=ship-only.sh ;;
  *) echo "Usage: bash verify25.sh check | run TOOL | ship TOOL"; exit 2 ;;
esac
echo "ONE MANUAL CASE: $tool / slot025 / $action"
exec bash "$base/$key/$script"
