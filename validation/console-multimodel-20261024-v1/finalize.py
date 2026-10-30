"""Finalize evidence and source hashes; does not grant execution permission."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import console_bridge_v3 as b
HERE=Path(__file__).resolve().parent
snapshots={}
for name,p in [('v2_and_school',HERE/'preservation-before.json'),('historical_6320',ROOT/'validation/console-openrouter-20261024-v1/preservation-before.json')]:
    before=b.read(p);changes=[n for n,h in before.items() if not (ROOT/n).is_file() or b.sha(ROOT/n)!=h]
    snapshots[name]=dict(files=len(before),changes=changes)
    if changes:raise ValueError(name+': '+str(changes[:5]))
b.save(HERE/'preservation-final.json',snapshots)
sources=b.bridge_bindings()
for n in ('Open-Lab-v3.cmd','Open-Lab-v3.ps1','test_console_multimodel.py','CONSOLE_MULTIMODEL_V3.md'):
    sources[n]=b.sha(ROOT/n)
b.save(HERE/'delivery-source-lock.json',sources)
evidence={str(p.relative_to(HERE)):b.sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='evidence-lock.json'}
b.save(HERE/'evidence-lock.json',evidence)
print(json.dumps(dict(sources=len(sources),evidence_files=len(evidence),preservation=snapshots,model_calls=0,school_tool_calls=0,execution_release=False),indent=2))
