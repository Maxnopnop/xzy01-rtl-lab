#!/usr/bin/env bash
set -eu
ece_synth_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ece_synth_dir/ece_synth_school.py" menu --shared-dir "$ece_synth_dir" "$@"
