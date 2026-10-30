#!/usr/bin/env bash
set -eu
local_synth_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$local_synth_dir"
export PYTHONUNBUFFERED=1
printf "LOCAL START: %s\n" "$local_synth_dir"
printf "Single-case %s; results remain in local returned/ (no Horizon access during run).\n" "dc"
exec python3 -u "$local_synth_dir/ece_synth_school.py" menu --shared-dir "$local_synth_dir" --package-id synth-dc-20261009T100543Z-d47c8919 --return-dir "$local_synth_dir/returned"
