import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
paths=[p for d in ('reuse',) for p in (P/d).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
paths += [P/n for n in ('runner.py','Start-Experiments.ps1','batch.json','parent-evidence-lock.json','reuse-provenance.json','tests.py','tool-discovery.json')]
paths += [P/n for n in ('route-config.json','slot-mapping.json','migration-provenance.json')]
lock={p.relative_to(P).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with (P/'source-lock-r1.json').open('x',encoding='utf-8') as f:json.dump(lock,f,indent=2)
