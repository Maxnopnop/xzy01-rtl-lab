"""Single archive staging/flat import, reusing the console's validated pack/collect."""
import json
from pathlib import Path
import shutil
import zipfile
from integration import b, school, HERE

def prepare(record):
    folder=Path(record['local']);shared=Path(record['shared']).parent
    for n,h in record['files'].items():b.require(b.sha(folder/n)==h,'本机原包变化')
    members={n:(folder/n).read_bytes() for n in record['files']}
    members['home_one.py']=(HERE/'home_one.py').read_bytes()
    members['home-lock.json']=b.canonical({n:b.digest(raw) for n,raw in members.items()})
    archive=folder.parent/(record['key']+'-home.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for n,raw in members.items():z.writestr(n,raw)
    target=shared/archive.name
    with target.open('xb') as f:f.write(archive.read_bytes())
    b.require(b.sha(target)==b.sha(archive),'单 ZIP 复制失败')
    out=dict(record,home_archive=str(archive),shared_archive=str(target),home_sha256=b.sha(archive))
    b.save(folder.parent/(record['key']+'-home-record.json'),out)
    return out

def command(record,action='check'):
    b.require(action in ('check','run','ship'),'无效动作')
    key=b.safe_id(record['key']);digest=record['home_sha256']
    b.require(b.re.fullmatch('[a-f0-9]{64}',digest),'ZIP hash 无效')
    b.require(b.sha(record['shared_archive'])==digest,'共享 ZIP 改变')
    name=Path(record['shared_archive']).name
    b.require(name==key+'-home.zip','归档名称无效')
    # Check copies one file, checks its external frozen digest, then validates safe members.
    # No packaged code is run until archive SHA is verified. All execution paths are HOME.
    if action=='check':
        code="""import hashlib,json,shutil,stat,sys,zipfile
from pathlib import Path
src=Path(sys.argv[1]); expected=sys.argv[2]; key=sys.argv[3]
dest=Path.home()/'xzy01-console-staged'/key
raw=src.read_bytes()
if len(raw)>32*1024**2 or hashlib.sha256(raw).hexdigest()!=expected:raise SystemExit('STOP: ZIP hash/size')
with zipfile.ZipFile(src) as z:
 items=z.infolist()
 if len({i.filename for i in items})!=len(items) or sum(i.file_size for i in items)>32*1024**2:raise SystemExit('STOP: members/size')
 if any(Path(i.filename).name!=i.filename or '/' in i.filename or '\\\\' in i.filename or stat.S_ISLNK(i.external_attr>>16) for i in items):raise SystemExit('STOP: unsafe member')
 if z.testzip() is not None:raise SystemExit('STOP: CRC')
 if dest.exists():
  if any(not (dest/i.filename).is_file() or (dest/i.filename).read_bytes()!=z.read(i) for i in items):raise SystemExit('STOP: existing staged files differ')
 else:
  dest.mkdir(parents=True)
  for i in items:(dest/i.filename).write_bytes(z.read(i))
print('STAGED IN HOME: '+str(dest))
"""
        return '( set -e\np=$(find "$HOME/tsclient" -maxdepth 6 -type f -name "'+name+'" -print -quit); test -n "$p"\npython3 - "$p" '+digest+' '+key+" <<'PY'\n"+code+'PY\npython3 "$HOME/xzy01-console-staged/'+key+'/home_one.py" check\n)'
    return command(record,'check')+' && ( p=$(find "$HOME/tsclient" -maxdepth 6 -type f -name "'+name+'" -print -quit); test -n "$p" && python3 "$HOME/xzy01-console-staged/'+key+'/home_one.py" '+action+' "$(dirname "$p")" )'

def collect_flat(record,sidecar):
    sidecar=Path(sidecar);meta=b.read(sidecar)
    b.require(meta['key']==record['key'] and meta['manifest_sha256']==record['manifest_sha256'],'回传 key/manifest 不符')
    archive=sidecar.with_suffix('.zip')
    b.require(b.sha(archive)==meta['archive_sha256'],'平铺 ZIP hash 不符')
    inbox=b.STATE/'flat-inbox'/record['key']/meta['archive_sha256']
    inbox.mkdir(parents=True,exist_ok=True)
    for src,name in ((sidecar,'console-return.json'),(archive,'console-return.zip')):
        dst=inbox/name
        if dst.exists():b.require(b.sha(dst)==b.sha(src),'本机已有不同回传')
        else:
            with dst.open('xb') as f:f.write(src.read_bytes())
    return school.collect(record,inbox/'console-return.json')
