"""One-time post-process lock finalization after Windows run.lock is released."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(HERE)]
import batch,rtl_lab as lab,r2
def main():
    run=r2.RUN;plan=r2.verify(run);assert not (run/'evidence-lock.json').exists()
    assert batch.read(run/'dispatch.json')==dict(status='GENERATION_COMPLETE',gate=True)
    s=batch.read(run/'summary.json');assert s['started']==s['planned']==len(s['rows'])==20
    for j,row in zip(plan['jobs'],s['rows']):
        folder=run/'jobs'/j['id'];g=batch.read(folder/'generation.json');assert g['status']=='GENERATED' and j['id']==row['id']
        assert lab.digest((folder/'response.txt').read_bytes())==g['response_sha256']
        assert batch.read(folder/'judge.json')['status']==row['status']
    # The original CLI process has exited; including released lock bytes is now safe.
    hashes={str(p.relative_to(run)):lab.digest(p.read_bytes()) for p in run.rglob('*') if p.is_file()}
    batch.atomic(run/'evidence-lock.json',hashes)
    batch.atomic(HERE/'r2-finalization.json',dict(status='PASS',action='POST_PROCESS_EVIDENCE_LOCK_ONLY',files=len(hashes),model_calls=0,icarus_evaluations=0,reason='Windows locked-file read failure after complete scoring'))
    print('Finalized',len(hashes),'files; no generation or scoring repeated')
if __name__=='__main__':main()
