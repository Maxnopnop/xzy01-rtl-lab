#!/bin/bash
# Works when called from a tcsh terminal via: bash /path/to/ece_menu.sh
set -eu
transfer_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$transfer_dir/ece_station.py" --shared-dir "$transfer_dir" "$@"
