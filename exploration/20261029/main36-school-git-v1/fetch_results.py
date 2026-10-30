"""Fetch allowlisted return blobs only; no remote code execution or EDA."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;REPO=P/'repo';SCHOOL=P.parent/'main36-school-v1'
def git(args):
 r=subprocess.run(['git','-c','credential.helper=','-c','credential.helper=!gh auth git-credential']+args,cwd=REPO,capture_output=True)
 if r.returncode:raise ValueError('Git '+args[0]+' failed; no tool executed')
 return r.stdout
def blob(ref,name,limit):
 if int(git(['cat-file','-s',ref+':'+name]))>limit:raise ValueError('Oversized return')
 return git(['cat-file','blob',ref+':'+name])
def main():
 prefix='school-results/main36-v1/'
 refs=git(['ls-remote','--heads','origin','refs/heads/'+prefix+'*']).decode().splitlines()
 if not refs:print('No Git returns yet; EDA calls=0');return 0
 git(['fetch','origin','refs/heads/'+prefix+'*:refs/remotes/origin/'+prefix+'*'])
 source=json.loads((P/'published.json').read_bytes())['commit'];index=json.loads((REPO/'case-index.json').read_bytes());keys={r['key']:r for r in index['cases']}
 inbox=P/'git-inbox';inbox.mkdir(exist_ok=True)
 for line in refs:
  _,remote=line.split();key=remote.rsplit('/',1)[1]
  if key not in keys:raise ValueError('Unrecognized return key')
  ref='refs/remotes/origin/'+prefix+key;base='returns/'+key+'/'
  names=git(['ls-tree','-r','--name-only',ref]).decode().splitlines()
  expected=[base+'provenance.json',base+'return-'+key+'.json',base+'return-'+key+'.zip']
  if set(names)!=set(expected):raise ValueError('Unexpected result branch files')
  prov=json.loads(blob(ref,expected[0],65536))
  if prov['input_commit']!=source or prov['bundle_sha256']!='b5a9a138b78952b4c2ae7c639b8518ca070cf7838453efd6ef2a9cd8ff8d441b':raise ValueError('Input commit mismatch')
  raw=blob(ref,expected[1],65536);meta=json.loads(raw);archive=blob(ref,expected[2],100*1024**2)
  if meta['key']!=key or meta['manifest_sha256']!=keys[key]['manifest_sha256'] or hashlib.sha256(archive).hexdigest()!=meta['archive_sha256']:raise ValueError('Return hash mismatch')
  for name,data in [('return-'+key+'.json',raw),('return-'+key+'.zip',archive)]:
   f=inbox/name
   if f.exists():
    if f.read_bytes()!=data:raise ValueError('Conflicting existing return')
   else:
    with f.open('xb') as stream:stream.write(data)
 return subprocess.call([sys.executable,'-B',str(SCHOOL/'collect.py'),'--shared',str(inbox)])
if __name__=='__main__':sys.exit(main())
