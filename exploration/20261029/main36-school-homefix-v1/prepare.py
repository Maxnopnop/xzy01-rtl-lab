"""Versioned HOME-alias fix; preserve task IDs, original RTL/TB/SDC and work dirs."""
import copy,hashlib,json,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent;OLD=P.parent/'main36-school-v1';GIT=P.parent/'main36-school-git-v1';repo=P/'repo';repo.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def raw(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(v)
def put(p,v):raw(p,json.dumps(v,ensure_ascii=False,indent=2).encode())
assert all(sha(OLD/n)==h for n,h in read(OLD/'delivery-lock.json').items())
parent={str(OLD/n):sha(OLD/n) for n in ('records.json','delivery-lock.json','main36-school-v1.zip')}
put(P/'parent-lock.json',parent)
for f in (OLD/'reuse').iterdir():
 if f.is_file():raw(P/'reuse'/f.name,f.read_bytes())
runner=(OLD/'reuse/console_school_runner_v3.py').read_text()
assert "if root.parent!=Path.home()/'xzy01-console-v3'" in runner
runner=runner.replace("if root.parent!=Path.home()/'xzy01-console-v3'", "if root.parent!=Path.home().resolve()/'xzy01-console-v3-homefix-v1'")
stage=(OLD/'reuse/console_stage_v3.py').read_text().replace("/'xzy01-console-v3'/key","/'xzy01-console-v3-homefix-v1'/key")
records=copy.deepcopy(read(OLD/'records.json'));out=P/'payload';out.mkdir()
for item in records:
 rec=item['record'];src=Path(rec['local']);dest=P/'state/school'/rec['key'];dest.mkdir(parents=True)
 for f in src.iterdir():
  if f.is_file() and f.name!='transfer-lock.json':raw(dest/f.name,f.read_bytes())
 # Development copy only; old package remains byte-identical.
 (dest/'console_school_runner_v3.py').write_text(runner,encoding='utf-8',newline='\n')
 (dest/'console_stage_v3.py').write_text(stage,encoding='utf-8',newline='\n')
 manifest=read(dest/'console-manifest.json');old_mh=sha(dest/'console-manifest.json')
 manifest['inputs']['console_school_runner_v3.py']=sha(dest/'console_school_runner_v3.py')
 (dest/'console-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n');mh=sha(dest/'console-manifest.json')
 for name in ('run-one.sh','ship-only.sh','check-share.sh'):
  text=(dest/name).read_text().replace(old_mh,mh);(dest/name).write_text(text,encoding='utf-8',newline='\n')
 files={f.name:sha(f) for f in dest.iterdir() if f.is_file()};put(dest/'transfer-lock.json',files)
 archive=out/(rec['key']+'.zip')
 with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(dest.iterdir()):z.write(f,f.name)
 rec.update(local=str(dest),shared=str(out),manifest_sha256=mh,files=files,archive=archive.name,archive_sha256=sha(archive),transport='GIT_HOME_FIX_V1')
 for n in ('stage_script','stage_sha256'):rec.pop(n,None)
 for name in ('dut.sv','testbench.sv','reference.sv','constraints.sdc','job.json','synthesis.tcl'):
  if (src/name).exists():assert (src/name).read_bytes()==(dest/name).read_bytes()
put(P/'records.json',records)
index=read(OLD/'outgoing/index.json')
for item in index['cases']:
 rec=next(r['record'] for r in records if r['ordinal']==item['ordinal'] and r['tool']==item['tool'])
 item['manifest_sha256']=rec['manifest_sha256'];item['archive_sha256']=rec['archive_sha256']
raw(out/'console_stage_v3.py',stage.encode());put(out/'index.json',index)
put(out/'bundle-lock.json',{f.name:sha(f) for f in out.iterdir() if f.is_file()})
archive=repo/'main36-school-v1.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(out.iterdir()):z.write(f,f.name)
for name in ('.gitattributes','.gitignore','README.md','ALL_COMMANDS.md','school_case.py','git_transport.py'):
 text=(GIT/'repo'/name).read_text(encoding='utf-8')
 text=text.replace('xzy01-main36-school-v1','xzy01-main36-school-homefix-v1')
 text=text.replace('school-results/main36-v1/','school-results/main36-homefix-v1/')
 text=text.replace('xzy01-main36-git-outbox','xzy01-main36-git-homefix-outbox').replace('xzy01-main36-git-uploads','xzy01-main36-git-homefix-uploads')
 text=text.replace("git(['remote','get-url','origin'])", "git(['config','--get','remote.origin.url'])")
 raw(repo/name,text.encode())
put(repo/'case-index.json',index)
for name in ('collect.py','Collect-Results.ps1'):raw(P/name,(OLD/name).read_bytes())
fetch=(GIT/'fetch_results.py').read_text().replace("SCHOOL=P.parent/'main36-school-v1'","SCHOOL=P")
fetch=fetch.replace('school-results/main36-v1/','school-results/main36-homefix-v1/').replace('b5a9a138b78952b4c2ae7c639b8518ca070cf7838453efd6ef2a9cd8ff8d441b',sha(archive))
raw(P/'fetch_results.py',fetch.encode());raw(P/'Fetch-Results.ps1',(GIT/'Fetch-Results.ps1').read_bytes())
note='''
HOME alias repair: resolve the HOME prefix before comparing it with the resolved script parent. Stage packages under xzy01-console-v3-homefix-v1 and the bundle under xzy01-main36-school-homefix-v1. Preserve old stages and the SAME xzy01-console-single/<key> execution directories; previously attempted tool jobs still cannot be rerun. Outputs use a new outbox/result branch because package hashes changed. No RTL/test/reference/SDC or synthesis Tcl changes.
Old Git compatibility: use cd then git checkout COMMIT; return upload reads remote.origin.url with git config --get, not remote get-url.
'''
with (repo/'README.md').open('a',encoding='utf-8') as f:f.write(note)
put(repo/'transport-lock.json',{f.name:sha(f) for f in repo.iterdir() if f.is_file()})
put(P/'delivery-lock.json',{f.relative_to(P).as_posix():sha(f) for d in ('reuse','state/school') for f in (P/d).rglob('*') if f.is_file()} | {n:sha(P/n) for n in ('records.json','collect.py','Collect-Results.ps1')})
put(P/'prepared.json',{'packages':144,'same_task_ids':True,'unchanged_data':['dut.sv','testbench.sv','reference.sv','constraints.sdc','job.json','synthesis.tcl'],'bundle_sha256':sha(archive),'model_calls':0,'school_calls':0})
print(json.dumps(read(P/'prepared.json')))
