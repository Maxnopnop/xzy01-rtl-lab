import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;repo=P/'repo'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
readme='''# Main36 school Git transport

This private transfer branch contains only the frozen 144 single-tool packages for 36 RTL outputs and transport code. No API key, generation ledger, commercial tool binaries or PDK libraries are included. The input ZIP is unchanged from the shared-folder delivery.

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

Results stay in `$HOME/xzy01-console-single` and are copied to `$HOME/xzy01-main36-git-outbox`. No tsclient mount is needed. Upload completed returns separately (no EDA):

```bash
python3 "$HOME/xzy01-main36-git/git_transport.py" push
```

Each return goes to its own `school-results/main36-v1/console-...` branch. HEAD, index, current worktree and main branch are not changed. If upload fails, retry only push, never EDA. Git credential prompts use the terminal; never embed a token in URLs or scripts. Use authorized private-repository credentials locally; do not send keys in chat.

If a local copy to outbox failed, transfer only:

```bash
python3 "$HOME/xzy01-main36-git/school_case.py" ship 001 vcs
```

Status:

```bash
python3 "$HOME/xzy01-main36-git/school_case.py" status
```

Nangate typical smoke constraints only, not formal PPA/timing signoff. Original test/sample-count mismatches and failures remain. Input 36 outputs include local failures. No new models or EDA run merely by stage/check/push. Stage verifies ZIP and all files and refuses differing existing HOME files. Git automatic line-ending conversion is disabled via `.gitattributes`.
'''
(repo/'README.md').write_text(readme,encoding='utf-8')
commands=(P.parent/'main36-school-v1/ALL_COMMANDS.md').read_text(encoding='utf-8').replace('$HOME/xzy01-main36-school-v1/school_main.py','$HOME/xzy01-main36-git/school_case.py')
(repo/'ALL_COMMANDS.md').write_text(commands,encoding='utf-8')
for n in ('school_case.py','git_transport.py'):ast.parse((repo/n).read_text(),feature_version=(3,6))
lock={p.name:sha(p) for p in repo.iterdir() if p.is_file()}
with (repo/'transport-lock.json').open('x',encoding='utf-8') as f:json.dump(lock,f,indent=2)
print(json.dumps({'files':len(lock)+1,'zip_sha256':sha(repo/'main36-school-v1.zip')}))
