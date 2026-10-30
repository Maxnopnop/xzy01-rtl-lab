import hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;old=P.parent/'main36-school-v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in read(P/'parent-lock.json').items():assert sha(Path(name))==h
for name,h in read(old/'delivery-lock.json').items():assert sha(old/name)==h
for name,h in read(P/'delivery-lock.json').items():assert sha(P/name)==h
for name,h in read(P/'repo/transport-lock.json').items():assert sha(P/'repo'/name)==h
before=read(old/'records.json');after=read(P/'records.json');count=0
for a,b in zip(before,after):
 assert a['record']['key']==b['record']['key']
 for name in ('dut.sv','testbench.sv','reference.sv','constraints.sdc','job.json','synthesis.tcl'):
  f=Path(a['record']['local'])/name
  if f.exists():assert f.read_bytes()==(Path(b['record']['local'])/name).read_bytes();count+=1
sys.path.insert(0,str(P/'reuse'))
import console_bridge_v3 as bridge,console_school_v3 as school
bridge.STATE=P/'offline-collector'
r=school.collect(after[0]['record'],next((P/'offline-mock-return').glob('*.json')))
assert r['status']=='FUNCTION_FAIL' and r['verified']
(P/'preservation-audit.json').write_text(json.dumps(dict(packages=len(after),unchanged_data_files=count,old_delivery_lock_verified=True,new_delivery_lock_verified=True,synthetic_failure_import_verified=True,model_calls=0,school_calls=0),indent=2))
print('Preservation and synthetic negative-result import verified')
