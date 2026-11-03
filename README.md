# Frozen 34-cell school sampling diagnostics

Transport-only branch. The ZIP is byte-identical to the 2026-10-31 package.
17 independent specimens x VCS/Xcelium, serial, one attempt, no model calls.
Run `bash start.sh` only after checking the pinned Git commit.
Existing package/state directories block the launch; do not delete them to bypass this.
Original RTL, tests, failed attempts and production scores remain unchanged.

Results are retained under `$HOME/xzy01-sampling-school34-v1`.
The frozen runner exports into `exports` before copying to `$HOME/tsclient/FYP/sampling-school34-v1`.
Only `SHARED_COPY_HASH_VERIFIED` confirms the remote shared copy matches; local Windows receipt verification is still required.
If shared transfer fails, preserve the local export and rerun export only:
`python3 -B "$HOME/xzy01-sampling-school34-package-v1/run.py" export`
This does not rerun EDA.

Prior offline diagnostic checks passed. Default regression retained 3 failures, 1 error and 2 skips among 24 tests; not all-green. School commercial-tool execution remains pending.
