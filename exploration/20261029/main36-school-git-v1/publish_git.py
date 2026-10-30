"""User-authorized private transfer branch; never modifies the existing checkout."""
import hashlib,json,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;repo=P/'repo';branch='ece-transfer/main36-school-v1-20261029';url='https://github.com/Maxnopnop/xzy01-rtl-lab.git'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(args):
 env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0'
 r=subprocess.run(['git','-c','credential.helper=','-c','credential.helper=!gh auth git-credential']+args,cwd=repo,capture_output=True,env=env,timeout=90)
 if r.returncode:raise RuntimeError('Git '+args[0]+' failed; no automatic retry. '+r.stderr.decode(errors='replace')[:800])
 return r.stdout
assert read(P/'offline-audit.json')['passed']
assert all(sha(Path(n))==h for n,h in read(P/'parent-lock.json').items())
assert git(['status','--porcelain'])==b''
names=git(['ls-tree','-r','--name-only','HEAD']).decode().splitlines()
expected={'.gitattributes','.gitignore','ALL_COMMANDS.md','README.md','case-index.json','git_transport.py','school_case.py','main36-school-v1.zip','transport-lock.json'}
assert set(names)==expected
for n in names:assert git(['cat-file','blob','HEAD:'+n])==(repo/n).read_bytes()
git(['remote','add','origin',url])
assert not git(['ls-remote','--heads','origin','refs/heads/'+branch]),'Existing branch: refuse replacement'
commit=git(['rev-parse','HEAD']).decode().strip()
git(['push','origin','HEAD:refs/heads/'+branch])
assert git(['ls-remote','--heads','origin','refs/heads/'+branch]).decode().split()[0]==commit
out={'repository':url,'private_verified':True,'branch':branch,'commit':commit,'files':{n:sha(repo/n) for n in names},'old_parent_unchanged':True,'main_branch_modified':False,'model_calls':0,'eda_calls':0}
with (P/'published.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
print(json.dumps({'branch':branch,'commit':commit,'files':len(names),'pushed':True}))
