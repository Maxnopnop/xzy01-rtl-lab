import contextlib,importlib.util,io,json,shutil,subprocess,sys
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;T=P/'offline-transport';T.mkdir(exist_ok=False)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
subprocess.run(['git','clone','--no-hardlinks',str(P/'repo'),str(T/'clone')],check=True,capture_output=True)
subprocess.run(['git','init','--bare',str(T/'remote.git')],check=True,capture_output=True)
clone=T/'clone';home=T/'home';home.mkdir();mod=load('git_school_test',clone/'git_transport.py')
git(clone,'remote','set-url','origin',mod.REMOTE)
before=git(clone,'rev-parse','HEAD');status_before=git(clone,'status','--porcelain')
checks=[]
def check(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
with patch.object(Path,'home',return_value=home),contextlib.redirect_stdout(io.StringIO()):
 dest=mod.stage();check('Stage HOME without tsclient',dest.exists() and not (home/'tsclient').exists())
 mod.stage();check('Repeat identical stage allowed',True)
case=load('case_git_test',clone/'school_case.py');case.BASE=dest
check('Offline case check has no shared mount dependency',case.checks(dest,school=False)['status']=='READY_FOR_ONE_MANUAL_CASE' and 'tsclient/FYP' not in (clone/'school_case.py').read_text())
mock=P/'offline-mock-return'
for f in mock.iterdir():shutil.copyfile(f,home/'xzy01-main36-git-homefix-outbox'/f.name)
pushes=[];real_run=subprocess.run
def mock_push(cmd,**kwargs):
 check('Only explicit Git push invokes transport',cmd[:3]==['git','push','origin'])
 pushes.append(cmd)
 return real_run(['git','push',str(T/'remote.git'),cmd[3]],cwd=kwargs['cwd'],capture_output=True).returncode
with patch.object(Path,'home',return_value=home),patch.object(mod.subprocess,'call',mock_push),contextlib.redirect_stdout(io.StringIO()):
 check('Return push succeeds via local bare fixture',mod.push()==0)
 check('Identical return push skips prior sent record',mod.push()==0)
check('Only one push, no EDA',len(pushes)==1)
check('HEAD and original index/worktree unchanged',git(clone,'rev-parse','HEAD')==before and git(clone,'status','--porcelain')==status_before)
ref=git(T/'remote.git','for-each-ref','--format=%(refname)','refs/heads/school-results/').decode().strip()
names=git(T/'remote.git','ls-tree','-r','--name-only',ref).decode().splitlines()
check('Result branch contains only 3 return data files',len(names)==3 and all(n.startswith('returns/') for n in names))
f=load('git_fetch_test',P/'fetch_results.py');f.REPO=clone;f.P=T/'fetch';f.P.mkdir()
(f.P/'published.json').write_text(json.dumps({'commit':before.decode().strip()}))
git(clone,'remote','set-url','origin',str(T/'remote.git'))
calls=[]
with patch.object(f.subprocess,'call',side_effect=lambda cmd:calls.append(cmd) or 0):check('Fetch result data from local bare fixture',f.main()==0)
check('Importer only receives local inbox',len(calls)==1 and calls[0][-2]=='--shared')
check('Fetched return bytes identical',all((f.P/'git-inbox'/p.name).read_bytes()==p.read_bytes() for p in mock.iterdir()))
(dest/'index.json').write_text('tampered')
with patch.object(Path,'home',return_value=home):
 try:mod.stage();rejected=False
 except ValueError:rejected=True
check('Different existing HOME refused',rejected)
with (P/'offline-audit.json').open('x',encoding='utf-8') as stream:json.dump({'passed':True,'checks':checks,'model_calls':0,'eda_calls':0,'external_network_calls':0,'synthetic_returns_only':True},stream,indent=2)
print(json.dumps({'passed':True,'checks':len(checks),'external_network_calls':0,'eda_calls':0}))
