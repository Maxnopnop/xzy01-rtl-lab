# Main36 school Git transport

This public transfer branch contains only the frozen 144 single-tool packages for 36 RTL outputs and transport code. No API key, generation ledger, commercial tool binaries or PDK libraries are included. This version changes HOME path validation and transport only; RTL, testbenches, references and synthesis constraints are unchanged.

After cloning and checking out the separately supplied exact commit, run:

```bash
python3 "$HOME/xzy01-main36-git/git_transport.py" stage
python3 "$HOME/xzy01-main36-git/school_case.py" check
python3 "$HOME/xzy01-main36-git/school_case.py" run 001 vcs
python3 "$HOME/xzy01-main36-git/school_case.py" run 001 xcelium
python3 "$HOME/xzy01-main36-git/school_case.py" run 001 dc
python3 "$HOME/xzy01-main36-git/school_case.py" run 001 genus
```

Run one command at a time, wait for completion. See ALL_COMMANDS.md for 001..036. No run-all scheduler. Stop on environment/license/timeout/unknown errors; do not rerun existing cases. This uses the SAME school package IDs as shared-folder mode, so already attempted cases remain protected. Do not run both entry points concurrently.

Results stay in `$HOME/xzy01-console-single` and are copied to `$HOME/xzy01-main36-git-homefix-outbox`. No tsclient mount is needed. Upload completed returns separately (no EDA):

```bash
python3 "$HOME/xzy01-main36-git/git_transport.py" push
```

Each return goes to its own `school-results/main36-homefix-v1/console-...` branch. HEAD, index, current worktree and main branch are not changed. If upload fails, retry only push, never EDA. Git credential prompts use the terminal; never embed a token in URLs or scripts. Downloading is public; uploading requires authorized repository write access. Do not send keys in chat.

If a local copy to outbox failed, transfer only:

```bash
python3 "$HOME/xzy01-main36-git/school_case.py" ship 001 vcs
```

Status:

```bash
python3 "$HOME/xzy01-main36-git/school_case.py" status
```

Nangate typical smoke constraints only, not formal PPA/timing signoff. Original test/sample-count mismatches and failures remain. Input 36 outputs include local failures. No new models or EDA run merely by stage/check/push. Stage verifies ZIP and all files and refuses differing existing HOME files. Git automatic line-ending conversion is disabled via `.gitattributes`.

HOME alias repair: resolve the HOME prefix before comparing it with the resolved script parent. Stage packages under xzy01-console-v3-homefix-v1 and the bundle under xzy01-main36-school-homefix-v1. Preserve old stages and the SAME xzy01-console-single/<key> execution directories; previously attempted tool jobs still cannot be rerun. Outputs use a new outbox/result branch because package hashes changed. No RTL/test/reference/SDC or synthesis Tcl changes.
Old Git compatibility: use cd then git checkout COMMIT; return upload reads remote.origin.url with git config --get, not remote get-url.
