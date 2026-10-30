"""Python3.6 Git stage/return transport only. Never launches EDA or models."""
import argparse,hashlib,json,os,re,stat,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REMOTE='https://github.com/Maxnopnop/xzy01-rtl-lab.git'
PREFIX='school-results/main36-v1/'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(obj,f,indent=2)
def git(args,data=None,env=None):
 r=subprocess.run(['git']+args,cwd=str(ROOT),input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
 if r.returncode:raise ValueError('Git '+args[0]+' failed; check network/authentication. No EDA was started.')
 return r.stdout
def verify():
 lock=read(ROOT/'transport-lock.json')
 for n,h in lock.items():
  if Path(n).name!=n or sha(ROOT/n)!=h:raise ValueError('Git payload changed: '+n)
 return lock
def stage():
 verify();archive=ROOT/'main36-school-v1.zip';dest=Path.home()/'xzy01-main36-school-v1'
 with zipfile.ZipFile(str(archive)) as z:
  infos=z.infolist();names=[i.filename for i in infos]
  if len(names)!=len(set(names)) or sum(i.file_size for i in infos)>100*1024**2:raise ValueError('Invalid archive size')
  if any(Path(n).name!=n or '\\' in n or ':' in n or n in ('.','..') for n in names):raise ValueError('Unsafe archive member')
  if any(stat.S_ISLNK(i.external_attr>>16) for i in infos):raise ValueError('Symlink rejected')
  lock=json.loads(z.read('bundle-lock.json'))
  if set(names)!=set(lock)|{'bundle-lock.json'}:raise ValueError('Unexpected archive member')
  for n,h in lock.items():
   if hashlib.sha256(z.read(n)).hexdigest()!=h:raise ValueError('Inner payload changed')
  dest.mkdir(parents=True,exist_ok=True)
  for n in names:
   p=dest/n
   if p.exists():
    if p.read_bytes()!=z.read(n):raise ValueError('Existing HOME content differs; no overwrite')
   else:
    with p.open('xb') as f:f.write(z.read(n))
 (Path.home()/'xzy01-main36-git-outbox').mkdir(exist_ok=True)
 print('HOME VERIFIED; local outbox ready; EDA calls=0')
 return dest
def make_commit(files):
 with tempfile.TemporaryDirectory(prefix='school-return-index-') as tmp:
  env=os.environ.copy();env['GIT_INDEX_FILE']=str(Path(tmp)/'index')
  env.update(GIT_AUTHOR_NAME='XZY01 School Transport',GIT_AUTHOR_EMAIL='school-transport@localhost',GIT_COMMITTER_NAME='XZY01 School Transport',GIT_COMMITTER_EMAIL='school-transport@localhost')
  git(['read-tree','--empty'],env=env)
  for name,raw in files.items():
   if not re.fullmatch(r'returns/console-[a-f0-9]{16}/(?:return-console-[a-f0-9]{16}\.(?:json|zip)|provenance.json)',name):raise ValueError('Invalid return path')
   blob=git(['hash-object','-w','--stdin'],data=raw).decode().strip()
   git(['update-index','--add','--cacheinfo','100644',blob,name],env=env)
  tree=git(['write-tree'],env=env).decode().strip()
  return git(['commit-tree',tree],data=b'Preserve one school tool return [skip ci]\n',env=env).decode().strip()
def push():
 verify()
 if git(['remote','get-url','origin']).decode().strip()!=REMOTE:raise ValueError('Unexpected remote; refuse upload')
 index=read(ROOT/'case-index.json');cases={r['key']:r for r in index['cases']}
 out=Path.home()/'xzy01-main36-git-outbox';state=Path.home()/'xzy01-main36-git-uploads';state.mkdir(exist_ok=True)
 lock=state/'push.lock'
 with lock.open('x') as f:f.write(str(os.getpid()))
 count=0
 try:
  for side in sorted(out.glob('return-console-*.json')):
   info=read(side);key=info.get('key');case=cases.get(key)
   if not case or info['manifest_sha256']!=case['manifest_sha256']:raise ValueError('Return not in frozen 144 cases')
   archive=out/('return-'+key+'.zip')
   if side.name!='return-'+key+'.json' or sha(archive)!=info['archive_sha256'] or archive.stat().st_size>100*1024**2:raise ValueError('Return bytes/hash invalid')
   mark=state/(key+'.json');sent=state/(key+'.sent.json');fingerprint=sha(side)+':'+sha(archive)
   if mark.exists():
    rec=read(mark)
    if rec['fingerprint']!=fingerprint:raise ValueError('Changed prior return; no overwrite')
   else:
    source=git(['rev-parse','HEAD']).decode().strip()
    files={'returns/'+key+'/'+p.name:p.read_bytes() for p in (side,archive)}
    files['returns/'+key+'/provenance.json']=json.dumps({'input_commit':source,'bundle_sha256':sha(ROOT/'main36-school-v1.zip'),'key':key}).encode()
    commit=make_commit(files);branch=PREFIX+key
    git(['update-ref','refs/heads/'+branch,commit])
    rec={'fingerprint':fingerprint,'commit':commit,'branch':branch};save(mark,rec)
   if sent.exists():continue
   # One explicit push; inherit terminal for Git's credential prompt. No retry loop.
   code=subprocess.call(['git','push','origin',rec['commit']+':refs/heads/'+rec['branch']],cwd=str(ROOT))
   if code:print('Return remains in HOME. Retry this push command only; do not rerun EDA.');return 2
   save(sent,rec);count+=1
  print(json.dumps({'new_returns_uploaded':count,'eda_calls':0,'model_calls':0}));return 0
 finally:lock.unlink()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['stage','push']);a=p.parse_args()
 if a.action=='stage':stage();return 0
 return push()
if __name__=='__main__':
 try:sys.exit(main())
 except Exception as e:print('STOP: '+str(e));sys.exit(2)
