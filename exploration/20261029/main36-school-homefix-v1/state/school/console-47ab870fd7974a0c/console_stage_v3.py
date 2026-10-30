"""Python 3.6+ fixed ZIP -> HOME, no EDA invocation, no arbitrary extraction."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import stat
import sys
import zipfile

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def stage(archive, expected, home=None):
    archive=Path(archive)
    if sha(archive)!=expected:raise ValueError('ZIP hash mismatch')
    with zipfile.ZipFile(str(archive)) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)) or sum(i.file_size for i in infos)>100*1024**2:raise ValueError('Invalid archive size/members')
        if any(Path(n).name!=n or '\\' in n or ':' in n or n in ('.','..') for n in names):raise ValueError('Unsafe member')
        if any(stat.S_ISLNK(i.external_attr>>16) for i in infos):raise ValueError('Symlink rejected')
        lock=json.loads(z.read('transfer-lock.json'))
        if set(names)!=set(lock)|{'transfer-lock.json'}:raise ValueError('Unexpected archive member')
        for n,h in lock.items():
            if hashlib.sha256(z.read(n)).hexdigest()!=h:raise ValueError('Input hash mismatch')
        manifest=json.loads(z.read('console-manifest.json'));key=manifest['key']
        if not re.fullmatch(r'console-[a-f0-9]{16}',key):raise ValueError('Bad package key')
        for n,h in manifest['inputs'].items():
            if lock.get(n)!=h:raise ValueError('Manifest input mismatch')
        dest=Path(home or Path.home())/'xzy01-console-v3-homefix-v1'/key
        if dest.exists():
            for n,h in lock.items():
                if sha(dest/n)!=h:raise ValueError('Existing HOME stage differs; no overwrite')
            if (dest/'transfer-lock.json').read_bytes()!=z.read('transfer-lock.json'):raise ValueError('Existing lock differs')
        else:
            dest.mkdir(parents=True,exist_ok=False)
            for n in names:
                with (dest/n).open('xb') as f:f.write(z.read(n))
    print('HOME VERIFIED; no EDA started: '+str(dest))
    return dest

if __name__=='__main__':stage(sys.argv[1],sys.argv[2])
