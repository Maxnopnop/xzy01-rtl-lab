"""Read-only verification of first preparation's historical byte baseline."""
import hashlib,json,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=HERE.parent/'fixed-input-direct-rtl-v1'
def main():
    started=time.monotonic();bad=[]
    baseline=json.loads((BASE/'prior-bindings.json').read_text(encoding='utf-8-sig'))
    for i,(name,expected) in enumerate(baseline.items(),1):
        p=ROOT/name
        actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        if actual!=expected:bad.append({'path':name,'expected':expected,'actual':actual})
        if i%5000==0:print(f'Checked {i}/{len(baseline)} historical files',flush=True)
    result={'status':'PASS' if not bad else 'FAIL','checked_files':len(baseline),'mismatches':bad,
            'baseline_sha256':hashlib.sha256((BASE/'prior-bindings.json').read_bytes()).hexdigest(),
            'scope':'Existing files in evidence/, exploration/20261011/, exploration/20261015/; not a global filesystem or Git-clean claim',
            'model_calls':0,'eda_calls':0,'elapsed_seconds':time.monotonic()-started}
    (HERE/'prior-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checked':len(baseline),'mismatches':len(bad)}))
    return int(bool(bad))
if __name__=='__main__':raise SystemExit(main())
