"""Offline saved-evidence reconstruction, new output only, never dispatches."""
import argparse,json,sys
from pathlib import Path
import stream_process as s
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE.parents[2]))
import batch
def recover(run,out):
    run=Path(run);out=Path(out)
    assert not out.exists() and run.resolve()!=out.resolve()
    rows=[]
    with batch.lock(run):
        for p in sorted((run/'jobs').glob('*/started.json')):
            folder=p.parent;call=folder/'call'
            if (folder/'generation.json').exists():
                rows.append(dict(id=folder.name,status='ORIGINAL_GENERATION_PRESENT',source_sha256=s.digest((folder/'generation.json').read_bytes())));continue
            r=s.recover(call)
            if r['status']=='ACTIVE_CHILD':raise RuntimeError('Associated child alive; no closure/reconstruction permitted')
            rows.append(dict(id=folder.name,**r))
        out.mkdir(parents=True)
        s.atomic(out/'recovery.json',dict(label='OFFLINE_SAVED_EVIDENCE_ONLY',model_calls=0,rows=rows,planned_denominator=len(s.read(run/'plan.json')['jobs']),unknown_usage=None,fees='UNKNOWN'))
        s.atomic(out/'evidence-lock.json',{p.name:s.digest(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('new_output');a=p.parse_args();recover(a.run,a.new_output)
