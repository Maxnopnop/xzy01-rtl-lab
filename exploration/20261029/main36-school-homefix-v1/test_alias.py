import ast, hashlib, importlib.util, json, shutil, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 assert v,n
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
stage=load('stage_fix',P/'payload/console_stage_v3.py')
index=json.loads((P/'repo/case-index.json').read_bytes());case=index['cases'][0]
base=Path(tempfile.mkdtemp(prefix='main36-homefix-offline-'))
real=base/'real';real.mkdir();alias=base/'alias';alias.symlink_to(real,target_is_directory=True)
out=real/'out';out.mkdir();calls=[]
def fake_execute(m,w,t):
 calls.append(m['key']);(w/'simulate.log').write_text('Mismatches: 1 in %s samples\n'%m['expected_checks'])
 return dict(status='FUNCTION_FAIL',returncode=0,mismatches=1,samples=m['expected_checks'])
oldstage=load('oldstage',P/'reuse/console_stage_v3.py')
oldarchive=P.parent/'main36-school-v1/outgoing'/case['archive']
oldroot=oldstage.stage(oldarchive,sha(oldarchive),home=alias)
old=load('oldrunner',oldroot/'console_school_runner_v3.py')
with patch.object(Path,'home',return_value=alias),patch.object(sys,'argv',['runner','run',str(out)]),patch.object(old,'execute',fake_execute):
 try:old.main();rejected=False
 except ValueError as e:rejected=str(e)=='Stage to HOME before execution'
check('Original alias bug reproduced before execute',rejected and not calls)
root=stage.stage(P/'payload'/case['archive'],case['archive_sha256'],home=alias)
runner=load('fixedrunner',root/'console_school_runner_v3.py')
with patch.object(Path,'home',return_value=alias),patch.object(sys,'argv',['runner','run',str(out)]),patch.object(runner,'execute',fake_execute):
 check('Alias accepted, synthetic failure retained',runner.main()==1 and len(calls)==1)
 try:runner.main();rejected=False
 except FileExistsError:rejected=True
 check('Duplicate attempt rejected',rejected and len(calls)==1)
foreign=base/'foreign'/case['key'];shutil.copytree(root,foreign)
bad=load('foreignrunner',foreign/'console_school_runner_v3.py')
with patch.object(Path,'home',return_value=alias),patch.object(sys,'argv',['runner','run',str(out)]),patch.object(bad,'execute',fake_execute):
 try:bad.main();rejected=False
 except ValueError:rejected=True
check('Outside HOME stage refused',rejected and len(calls)==1)
plain=base/'plain';plain.mkdir();plainout=plain/'out';plainout.mkdir()
plainroot=stage.stage(P/'payload'/case['archive'],case['archive_sha256'],home=plain)
normal=load('normalrunner',plainroot/'console_school_runner_v3.py')
with patch.object(Path,'home',return_value=plain),patch.object(sys,'argv',['runner','run',str(plainout)]),patch.object(normal,'execute',fake_execute):
 check('Non-alias HOME accepted',normal.main()==1 and len(calls)==2)
shells=0
for directory in (P/'state/school').iterdir():
 for f in directory.iterdir():
  if f.suffix=='.py':ast.parse(f.read_text(),feature_version=(3,6))
  if f.suffix=='.sh':subprocess.run(['bash','-n',str(f)],check=True);shells+=1
for f in (P/'repo').glob('*.py'):ast.parse(f.read_text(),feature_version=(3,6))
check('Python 3.6 syntax and all shell wrappers',shells==432)
mock=P/'offline-mock-return';mock.mkdir()
for f in out.iterdir():shutil.copyfile(f,mock/f.name)
(P/'alias-audit.json').write_text(json.dumps(dict(checks=checks,fixture_directory=str(base),synthetic_execute_calls=len(calls),real_eda_calls=0,model_calls=0),indent=2))
print(json.dumps(dict(checks=len(checks),shells=shells,real_eda_calls=0)))
