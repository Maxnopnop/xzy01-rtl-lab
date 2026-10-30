"""Read source and locks only. Never import target modules or invoke tools/models."""
import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];V2=R.with_name('handshake-dev-v2');R6=R.with_name('r6');PREP=R6/'runs/prepared-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (R/'source-lock.json').exists(),'No overwrite'
plan=read(PREP/'plan.json');assert sha(PREP/'plan.json')==read(PREP/'plan-lock.json')['sha256']=='f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4'
bindings={}
for name,h in plan['source_hashes'].items():
 p=ROOT/name;assert sha(p)==h,name;bindings[p.relative_to(ROOT).as_posix()]=h
for name,h in read(PREP/'preparation-lock.json').items():assert sha(PREP/name)==h,name
for p in [PREP/'plan.json',PREP/'plan-lock.json',PREP/'preparation-lock.json',ROOT/'fsm_ir.py']:
 bindings[p.relative_to(ROOT).as_posix()]=sha(p)
v2packet=read(V2/'packet-lock.json');assert sha(V2/'packet-lock.json')=='c614a32526e2fa0cb182be7b9dde7aca6e6249df54169a2b190da1f5569eaf16'
for name,h in v2packet.items():assert sha(V2/name)==h,name
excluded={'packet-lock.json','seal-verification.json','seal-audit.stdout.bin','seal-audit.stderr.bin'}
assert set(v2packet)=={p.relative_to(V2).as_posix() for p in V2.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
for p in V2.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:bindings[p.relative_to(ROOT).as_posix()]=sha(p)
save(R/'source-lock.json',bindings)
names=['fsm_ir.py','exploration/20261011/r6/engineering-v2/runner.py','exploration/20261011/r6/runner.py','exploration/20261011/r6/intent.py','exploration/20261011/r6/tasks.py','exploration/20261011/r6/judge.py','exploration/20261011/handshake-dev-v2/INTENT_COMPARISON_DESIGN.md','exploration/20261011/handshake-dev-v2/RESULTS.md','exploration/20261011/handshake-dev-v2/semantic-examples.json']
snapshot={n:dict(sha256=sha(ROOT/n),lines=[dict(line=i+1,text=t) for i,t in enumerate((ROOT/n).read_text(encoding='utf-8').splitlines())]) for n in names};save(R/'source-snapshot.json',snapshot)
# Static task declaration only, no import/evaluation of experiment code.
tree=ast.parse((R6/'tasks.py').read_text());task_names=None
for node in tree.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TASKS' for t in node.targets):task_names=[k.value for k in node.value.keys]
assert task_names==['ordered_retire','restoring_divide','tagged_join']
assert read(V2/'calibration-v2/summary.json')['all_expected'] is False
assert read(V2/'FAILURES.json')['calibration']['exit']==1
assert read(V2/'seal-verification.json')['default_regression_returncode']==1
save(R/'audit.json',dict(status='PASS_BOUNDED_READ_ONLY_DESIGN_BASIS_CORRECTION',scope='Static source and hash/line binding; no executable broadcast IR or classifier verification',r6_plan_sha256=sha(PREP/'plan.json'),r6_source_bindings=len(plan['source_hashes']),preparation_bindings=len(read(PREP/'preparation-lock.json')),source_bindings=len(bindings),v2_packet_sha256=sha(V2/'packet-lock.json'),v2_packet_bindings=len(v2packet),v2_all_files_preserved=len([p for p in V2.rglob('*') if p.is_file() and '__pycache__' not in p.parts]),task_names=task_names,source_snapshot_files=len(snapshot),legacy_fsm_domain='1bit Moore, not current R6',current_r6_domain='register/expression, possible finite broadcast representation but mapping UNKNOWN',intent_relation='DESIGN_ONLY_NOT_VERIFIED',original_examples=6,new_examples=0,original_calibration_exit=1,original_default_exit=1,compile_calls=0,simulate_calls=0,default_calls=0,ir_execution_calls=0,model_calls=0,candidate_expansion=0))
files={p.relative_to(R).as_posix():sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ('packet-lock.json','seal-verification.json')};save(R/'packet-lock.json',files)
for name,h in bindings.items():assert sha(ROOT/name)==h,name
for name,h in files.items():assert sha(R/name)==h,name
assert set(files)=={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and p.name not in ('packet-lock.json','seal-verification.json')}
save(R/'seal-verification.json',dict(status='PASS_HASH_AND_EXACT_PACKET_SET',packet_sha256=sha(R/'packet-lock.json'),packet_bindings=len(files),source_bindings=len(bindings),audit_sha256=sha(R/'audit.json'),read_only_old_sources=True,new_execution_calls=0))
print(json.dumps(read(R/'seal-verification.json')))
