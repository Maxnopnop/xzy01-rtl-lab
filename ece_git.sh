#!/usr/bin/env bash
set -eu
ece_repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$ece_repo_dir/ece_git.py" "$@"
