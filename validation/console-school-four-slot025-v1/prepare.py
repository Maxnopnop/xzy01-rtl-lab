"""Prepare four manual school cases using the console backend. No model/EDA calls."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
import console_bridge as b
import console_school as school

def write(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    shared=Path('C:/Users/A/Documents/FYP/ECE-Console-Verify25')
    shared.mkdir(exist_ok=False)
    row=next(r for r in b.historical_rows('new96') if r['ordinal']==25)
    origin=ROOT/'validation/next96-school-single-v1/next96-dc-slot025-v2'
    job=b.read(origin/'job.json');sdc=origin/'constraints.sdc'
    assert b.sha(sdc)==job['sdc_sha256']
    provenance=b.validate_saved_inputs(row)
    assert provenance['dut.sv']==job['rtl_sha256']
    shutil.copyfile(sdc,HERE/'constraints.sdc')
    base=job['profile'];profiles={tool:dict(base) for tool in ('dc','genus')}
    profiles['genus']['libraries']=[p.removesuffix('.db')+'.lib' for p in base['libraries']]
    b.save(HERE/'school-profile.json',dict(schema=1,tools=profiles,note='Same previously reviewed slot25 combinational smoke SDC; no PPA or clock constraint claim. Genus Liberty path confirmed by prior user terminal output; current readability checked on school.'))
    records={}
    (HERE/'records').mkdir()
    for tool in ('vcs','xcelium','dc','genus'):
        r=school.pack(row,tool,shared,profiles.get(tool),sdc if tool in profiles else None)
        records[tool]=r
        b.save(HERE/'records'/(tool+'.json'),r)
    b.save(HERE/'records.json',records)
    wrapper='''#!/usr/bin/env bash
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
action=${1:-check}
tool=${2:-}
if [ "$action" = check ]; then
  python3 "$base/check-all.py" "$base"
  exit $?
fi
case "$tool" in
'''
    for tool,r in records.items():wrapper+='  '+tool+') key='+r['key']+' ;;\n'
    wrapper+='''  *) echo "Select ONE tool: vcs xcelium dc genus"; exit 2 ;;
esac
case "$action" in
  run) script=run-one.sh ;;
  ship) script=ship-only.sh ;;
  *) echo "Usage: bash verify25.sh check | run TOOL | ship TOOL"; exit 2 ;;
esac
echo "ONE MANUAL CASE: $tool / slot025 / $action"
exec bash "$base/$key/$script"
'''
    write(shared/'verify25.sh',wrapper)
    setup={'vcs':'/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc','xcelium':'/usr/eelocal/cadence/xcelium2303hf/.cshrc','dc':'/usr/eelocal/synopsys/syn-vx2025.06-sp2/.cshrc','genus':'/usr/eelocal/cadence/genus211/.cshrc'}
    frozen={r['key']:r['files'] for r in records.values()}
    check='''# Python 3.6+, read-only preflight; starts no school tools.
import hashlib,json,os,shutil,sys
from pathlib import Path
base=Path(sys.argv[1]);errors=[]
'''+ 'files='+repr(frozen)+'\nsetups='+repr(setup)+'\nlibraries='+repr(profiles['dc']['libraries']+profiles['genus']['libraries'])+'\n'
    check+='''for key,items in files.items():
    for name,h in items.items():
        p=base/key/name
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append('PACKAGE: '+str(p))
for tool,p in setups.items():
    if not os.access(p,os.R_OK):errors.append('SETUP '+tool+': '+p)
for p in libraries:
    if not os.access(p,os.R_OK):errors.append('LIBRARY: '+p)
if not shutil.which('tcsh'):errors.append('tcsh missing')
if not shutil.which('sha256sum'):errors.append('sha256sum missing')
print(json.dumps(dict(status='READY_FOR_FOUR_MANUAL_COMMANDS' if not errors else 'BLOCKED',errors=errors,model_calls=0,tool_calls=0,license='not probed'),indent=2))
sys.exit(1 if errors else 0)
'''
    write(shared/'check-all.py',check)
    shutil.copyfile(shared/'verify25.sh',HERE/'verify25.sh')
    shutil.copyfile(shared/'check-all.py',HERE/'check-all.py')
    b.save(HERE/'prepared.json',dict(slot=25,task=row['task'],shared=str(shared),status='PREPARED_SCHOOL_NOT_RUN',tools=list(records),provenance=provenance,model_calls=0,school_tool_calls=0,shared_files={str(p.relative_to(shared)).replace('\\','/'):b.sha(p) for p in shared.rglob('*') if p.is_file()}))
    print(json.dumps(dict(shared=str(shared),tools=list(records),model_calls=0,school_tool_calls=0)))

if __name__=='__main__':main()
