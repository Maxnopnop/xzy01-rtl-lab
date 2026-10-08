#!/bin/bash
# Prepare ONE Xcelium case and inspect environment; does not run simulation.
set -eu
transfer_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
bash "$transfer_dir/start_ece.sh" "$transfer_dir/ece-xcelium-verify-20261008.zip"
