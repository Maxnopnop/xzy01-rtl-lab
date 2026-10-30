"""Offline verification only: never launches an experiment or deletes files."""
import argparse,hashlib,json,os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
root=Path(a.root).resolve()
if os.name=='nt' and not str(root).startswith('\\\\?\\'):root=Path('\\\\?\\'+str(root))
manifest=json.loads((root/'PROJECT_SYNC_MANIFEST.json').read_text(encoding='utf-8'))
def check(row):
 path=(root/row['path']).resolve()
 if not path.is_relative_to(root):return {'path':row['path'],'error':'outside root'}
 if not path.is_file():return {'path':row['path'],'error':'missing'}
 data=path.read_bytes()
 if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:return {'path':row['path'],'error':'hash/size mismatch'}
 return None
with ThreadPoolExecutor(max_workers=12) as pool:fail=[r for r in pool.map(check,manifest['files']) if r]
result={'passed':not fail,'checked':len(manifest['files']),'bytes':sum(r['bytes'] for r in manifest['files']),'failures':fail,'manifest_sha256':hashlib.sha256((root/'PROJECT_SYNC_MANIFEST.json').read_bytes()).hexdigest()}
Path(a.output).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));raise SystemExit(bool(fail))
