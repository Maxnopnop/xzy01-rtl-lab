#!/usr/bin/env bash
set -eu
elec_shared_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Run our helper locally in HOME; keep shared-folder access for transport only.
elec_helper_dir="$(mktemp -d "$HOME/elec-helper-XXXXXXXX")"
cp "$elec_shared_dir/elec_school.py" "$elec_shared_dir/elec_common.py" "$elec_helper_dir/"
exec python3 "$elec_helper_dir/elec_school.py" --shared-dir "$elec_shared_dir" "$@"
