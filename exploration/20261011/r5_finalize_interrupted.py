"""Close ONLY interrupted R5; never campaign/generate; frozen scorer only."""
import sys,json
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;BASE=P/'r5';ROOT=P.parents[1];sys.path[:0]=[str(BASE),str(ROOT)]
import runner,batch,rtl_lab as lab
RUN=runner.RUN;E=BASE/'interruption'
def forbidden(*args,**kwargs):raise AssertionError('No model/campaign/generate allowed in interrupted finalizer')
def main():
    proof=json.loads((E/'process-check.json').read_text(encoding='utf-8-sig'));assert proof['matched_processes']==[]
    p=runner.verify();assert batch.read(RUN/'plan-lock.json')['sha256']=='752be8b79f544a86f0961ab50e5a8645ea7d18132792670d9373e095fd295b4e'
    assert not (RUN/'evidence-lock.json').exists() and not (RUN/'dispatch.json').exists()
    before={str(x.relative_to(RUN)):lab.digest(x.read_bytes()) for x in RUN.rglob('*') if x.is_file() and x.name!='run.lock'}
    batch.atomic(E/'preserved-before-finalization.json',before)
    lock_bytes=(RUN/'run.lock').read_bytes();(E/'run-lock.original.bin').write_bytes(lock_bytes)
    batch.atomic(E/'lock-proof.json',dict(original_bytes=lock_bytes.hex(),sha256=lab.digest(lock_bytes),process_matches=0,action='Acquire existing OS advisory lock; no delete/truncate/rewrite',limitation='Persistent lock file alone is not active ownership'))
    assert len(list((RUN/'jobs').glob('*/started.json')))==21 and len(list((RUN/'jobs').glob('*/generation.json')))==20
    unknown=RUN/'jobs/escape_frame__r1__structured__regeneration';assert (unknown/'started.json').exists() and not (unknown/'generation.json').exists() and not (unknown/'response.txt').exists()
    with patch.object(runner.adapter,'generate_text',side_effect=forbidden),patch.object(runner,'generate',side_effect=forbidden),patch.object(runner,'campaign',side_effect=forbidden):
        with batch.lock(RUN):
            for rel,h in before.items():assert lab.digest((RUN/rel).read_bytes())==h,rel
            # Exact frozen campaign reservation recovery value, with no campaign dispatch.
            batch.atomic(unknown/'generation.json',dict(status='UNKNOWN_INTERRUPTED',usage=None,model_called=True,reservation_unknown=True))
            batch.atomic(RUN/'dispatch.json',dict(status='STOPPED_INFRASTRUCTURE',reason='Prior unknown/failed reservation',interruption='Original desktop turn interrupted; runner and linked CLI absent',unknown_job=unknown.name,known_generated=20,reserved_unknown=1,pending=27,model_calls_in_finalizer=0,provider_usage_for_unknown='UNKNOWN',finalized_utc=lab.utc()))
            summary=runner.score(RUN,p)
            assert summary['started']==21 and summary['statuses'].get('UNKNOWN_INTERRUPTED')==1 and summary['statuses'].get('PENDING')==27
            assert all(v['denominator']==6 for v in summary['strategies'].values())
        assert (RUN/'run.lock').read_bytes()==lock_bytes
        for rel,h in before.items():assert lab.digest((RUN/rel).read_bytes())==h,rel
        runner.seal(RUN)
    batch.atomic(E/'closure.json',dict(status='INTERRUPTED_BATCH_CLOSED',known_generated=20,reserved_unknown=1,pending=27,new_model_calls=0,previous_judges_reused=True,preserved_files=len(before),original_lock_unchanged=True,unknown_status='UNKNOWN_INTERRUPTED',provider_usage='UNKNOWN for missing21; do not replace None with zero',frozen_scorer='runner.score',source_hashes_unchanged=p['source_hashes']==runner.hashes(),sealed=True))
    print(json.dumps(batch.read(E/'closure.json'),indent=2))
if __name__=='__main__':main()
