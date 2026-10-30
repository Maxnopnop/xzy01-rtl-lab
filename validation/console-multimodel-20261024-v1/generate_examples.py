"""Offline demonstrator: export scripts, never execute inference/school tools."""
from pathlib import Path
import json
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import console_bridge_v3 as b
import console_school_v3 as school
import console_cli_v3 as cli
from test_console_multimodel import fixture
HERE=Path(__file__).resolve().parent
EX=HERE/'examples';EX.mkdir()
manifest=fixture(EX/'model-packet',3,actual_metadata=True)
release=EX/'NOT_RELEASED.json';b.save(release,dict(decision='NOT_RELEASED',user_approved=False,note='Offline fixture only; no authorization to call any model'))
cli.export_launcher(manifest,release,EX/'Start-One-NOT-RELEASED.ps1')
package=b.Package(manifest)
b.save(EX/'model-matrix.json',dict(models=package.data['models'],model_count=3,slots=6,budget_policy='calls_only',inference_availability='NOT_VERIFIED',execution_released=False))
share=EX/'shared-root';share.mkdir();sdc=EX/'SYNTHETIC.sdc';sdc.write_text('set_max_delay 10 -from [all_inputs] -to [all_outputs]\n')
row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
records={}
with patch.object(b,'STATE',EX/'local-state'):
    for tool in ('dc','genus','vcs','xcelium'):
        profile=dict(libraries=['/SYNTHETIC_NOT_FOR_EXECUTION/library.'+('db' if tool=='dc' else 'lib')],corner='OFFLINE_FIXTURE',constraints_reviewed=True,timeout_seconds=600)
        record=school.pack(row,tool,share,profile,sdc);records[tool]=record
        b.save(EX/(tool+'-record.json'),record)
        (EX/(tool+'-commands.txt')).write_text('# OFFLINE SCRIPT EXAMPLE ONLY. No school run authorized.\n# Stage and check only:\n'+school.command(record,'check')+'\n# One manual run (NOT EXECUTED):\n'+school.command(record,'run')+'\n# Ship existing result only:\n'+school.command(record,'ship')+'\n',encoding='utf-8')
b.save(EX/'records.json',records)
code="""import argparse,json
import console_school_v3 as school
import console_bridge_v3 as b
a=argparse.ArgumentParser();a.add_argument('--record',required=True);a.add_argument('--sidecar',required=True)
args=a.parse_args();print(json.dumps(school.collect(b.read(args.record),args.sidecar),ensure_ascii=False,indent=2))
"""
(EX/'Import-Flat-Return.py').write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\n'+code,encoding='utf-8')
b.save(EX/'example-file-hashes.json',{str(p.relative_to(EX)):b.sha(p) for p in EX.rglob('*') if p.is_file()})
print(json.dumps(dict(models=3,slots=6,school_packages=4,model_calls=0,school_tool_calls=0,output=str(EX)),indent=2))
