"""Read-only integrity + shell staging checks; never invokes the school runner."""
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import console_bridge_v3 as b
HERE=Path(__file__).resolve().parent
before=b.read(HERE/'preservation-before.json')
changed=[n for n,h in before.items() if not (ROOT/n).is_file() or b.sha(ROOT/n)!=h]
result=dict(protected_files=len(before),changed=changed,model_calls=0,school_tool_calls=0)
if changed:raise ValueError(changed)
records=b.read(HERE/'examples/records.json');checks=[]
home=subprocess.run(['wsl.exe','-d','Ubuntu','--exec','mktemp','-d'],capture_output=True,text=True,timeout=30,check=True).stdout.strip()
for tool,r in records.items():
    stage=Path(r['shared'])/r['stage_script']
    for name in ('run-one.sh','check-share.sh','ship-only.sh'):
        p=Path(r['local'])/name
        proc=subprocess.run(['wsl.exe','-d','Ubuntu','--exec','bash','-n',b.wsl_path(p)],capture_output=True,text=True,timeout=30)
        if proc.returncode:raise ValueError(proc.stderr)
    proc=subprocess.run(['wsl.exe','-d','Ubuntu','--exec','env','HOME='+home,'bash',b.wsl_path(stage)],capture_output=True,text=True,timeout=90)
    checks.append(dict(tool=tool,stage_sha256=b.sha(stage),returncode=proc.returncode,stdout=proc.stdout,stderr=proc.stderr))
    if proc.returncode:raise ValueError(proc.stderr)
result['wsl_home_staging']=checks
b.save(HERE/'integrity-and-wsl-stage.json',result)
print(json.dumps(result,indent=2))
