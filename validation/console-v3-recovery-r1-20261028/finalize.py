"""Read-only preservation audit then independent revision snapshot and lock."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import console_bridge_v3 as b
HERE=Path(__file__).resolve().parent
old=ROOT/'validation/console-multimodel-20261024-v1'
checks={}
def verify(label,lock,base):
    changes=[n for n,h in lock.items() if not (base/n).is_file() or b.sha(base/n)!=h]
    checks[label]=dict(files=len(lock),changes=changes)
    if changes:raise ValueError(label+': '+str(changes[:5]))
verify('original_v3_sources',b.read(old/'delivery-source-lock.json'),ROOT/'validation/console-v3-independent-review-20261028-v1/original-v3')
verify('original_v3_evidence',b.read(old/'evidence-lock.json'),old)
verify('v2_school',b.read(old/'preservation-before.json'),ROOT)
verify('historical',b.read(ROOT/'validation/console-openrouter-20261024-v1/preservation-before.json'),ROOT)
b.save(HERE/'preservation.json',checks)
bindings=b.bridge_bindings();b.save(HERE/'release-source-hashes.json',bindings)
names=list(b.read(old/'delivery-source-lock.json'))+['test_console_recovery_r1.py']
source=HERE/'source';source.mkdir()
for n in names:(source/n).write_bytes((ROOT/n).read_bytes())
b.save(HERE/'delivery-source-lock.json',{n:b.sha(ROOT/n) for n in names})
b.save(HERE/'evidence-lock.json',{str(p.relative_to(HERE)):b.sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
print(json.dumps(dict(revision='v3-recovery-r1-20261028',source_files=len(names),bridge_sha256=b.sha(ROOT/'console_bridge_v3.py'),transport_sha256=b.TRANSPORT_SHA,checks=checks),indent=2))
