"""Copy the original 48 frozen files into one ZIP, preserving their identities."""
import hashlib,json,shutil,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=read(HERE/'prepared.json');source=Path(p['shared']);shared=source.parent
    lock=p['shared_files']
    assert len(lock)==48 and all(sha(source/n)==h for n,h in lock.items())
    archive=HERE/'verify25-transfer-v1.zip'
    extra={'run-local.py':(HERE/'run-local.py').read_bytes(),'tool-keys.json':json.dumps({t:r['key'] for t,r in read(HERE/'records.json').items()}).encode()}
    hashes=dict(lock,**{n:hashlib.sha256(raw).hexdigest() for n,raw in extra.items()})
    extra['transfer-lock.json']=json.dumps(hashes,sort_keys=True).encode()
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for n in sorted(lock):z.write(source/n,n)
        for n,raw in extra.items():z.writestr(n,raw)
    expected=sha(archive)
    script='''#!/usr/bin/env bash
set -eu
base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
work="$HOME/xzy01-console-transfer-v1"
mkdir -p "$work"
if [ ! -f "$work/verify25-transfer-v1.zip" ]; then
  timeout 60s cp "$base/verify25-transfer-v1.zip" "$work/verify25-transfer-v1.zip"
fi
cd "$work"
printf '%s  %s\n' 'HASH_PLACEHOLDER' verify25-transfer-v1.zip | sha256sum -c -
python3 - <<'PY'
import hashlib,json,zipfile
from pathlib import Path
with zipfile.ZipFile('verify25-transfer-v1.zip') as z:
    names=z.namelist()
    if len(names)!=51 or len(set(names))!=51:raise ValueError('Archive members')
    for n in names:
        p=Path(n)
        if p.is_absolute() or '..' in p.parts or ':' in n or '\\' in n:raise ValueError('Unsafe name')
        raw=z.read(n)
        if p.exists():
            if p.read_bytes()!=raw:raise ValueError('Existing staged file changed: '+n)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(raw)
    for n,h in json.loads(z.read('transfer-lock.json').decode()).items():
        if hashlib.sha256(Path(n).read_bytes()).hexdigest()!=h:raise ValueError('Input hash: '+n)
print('STAGED: 48 original frozen files unchanged; no EDA started')
PY
exec python3 "$work/run-local.py" check
'''.replace('HASH_PLACEHOLDER',expected)
    # Preserve a literal backslash test inside the embedded Python.
    script=script.replace("or '\\' in n", "or '\\\\' in n")
    with (HERE/'verify25_stage.sh').open('x',encoding='utf-8',newline='\n') as f:f.write(script)
    for n in ('verify25_stage.sh','verify25-transfer-v1.zip'):
        with (shared/n).open('xb') as f:f.write((HERE/n).read_bytes())
        assert sha(shared/n)==sha(HERE/n)
    (HERE/'transfer-prepared.json').write_text(json.dumps(dict(original_files=48,archive_files=51,archive_sha256=expected,model_calls=0,school_tool_calls=0),indent=2))
    print(expected)

if __name__=='__main__':main()
