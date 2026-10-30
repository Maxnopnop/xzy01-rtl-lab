"""Persist offline delivery evidence; never call models or school tools."""
import ast
import collections
import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OUT=OUT/'delivery-final'
OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT))
import console_bridge as b
import console_school as school
from console_cli import export_launcher
from test_console_bridge import BridgeTests

rows=b.history()
b.save(OUT/'history-import.json',dict(counts=dict(collections.Counter(r['dataset'] for r in rows)),rows=rows,school=b.school_history(),model_calls=0))
fixture=BridgeTests();fixture.setUp()
try:
    packet=OUT/'example-unreleased-packet'
    shutil.copytree(fixture.base,packet)
    b.save(packet/'release.example.json',dict(decision='NOT_RELEASED',note='OFFLINE FIXTURE ONLY; requires coordinator review and source/manifest bindings. Do not edit this to bypass review.'))
    export_launcher(packet/'console-package.json',packet/'release.example.json',OUT/'Start-OpenRouter-One.EXAMPLE.ps1')
finally:fixture.doCleanups()
shared=OUT/'generated-school-preview/shared';shared.mkdir(parents=True)
sdc=OUT/'generated-school-preview/fixture.sdc'
sdc.write_text('# OFFLINE PACKAGING FIXTURE ONLY, NOT AN APPROVED TIMING CONSTRAINT\nset_max_delay 10 -from [all_inputs] -to [all_outputs]\n',encoding='utf-8')
row=next(r for r in rows if r['dataset']=='new96' and r['ordinal']==25)
records=[]
with patch.object(b,'STATE',OUT/'generated-school-preview'):
    for tool in ('vcs','xcelium','dc','genus'):
        profile=dict(libraries=['/OFFLINE_FIXTURE_NOT_A_LIBRARY/library.'+('db' if tool=='dc' else 'lib')],corner='OFFLINE_FIXTURE',constraints_reviewed=True,timeout_seconds=600)
        record=school.pack(row,tool,shared,profile,sdc)
        folder=Path(record['local'])
        ast.parse((folder/'console_school_runner.py').read_text(),feature_version=(3,6))
        records.append(dict(tool=tool,**record,commands={a:school.command(record,a) for a in ('run','check','ship')},offline_only=True,school_executed=False))
b.save(OUT/'generated-script-matrix.json',records)
before=b.read(b.STATE/'preservation-before.json')
changed=[p for p,h in before.items() if not Path(p).exists() or b.sha(p)!=h]
b.save(OUT/'preservation-after.json',dict(checked=len(before),changed=changed,passed=not changed))
if changed:raise SystemExit('Evidence drift: '+str(changed))
b.save(OUT/'delivery-source-lock.json',dict(b.bridge_bindings(),**{n:b.sha(ROOT/n) for n in ['Open-Lab-v2.cmd','Open-Lab-v2.ps1','test_console_bridge.py']}))
print(json.dumps(dict(history_rows=len(rows),school_packages=len(records),preserved_files=len(before),changed=changed,real_model_calls=0,school_eda_calls=0)))
