import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path[:0]=[str(ROOT),str(HERE)]
import r2,batch,rtl_lab as lab
def main():
    r2.verify(r2.RUN);report=[]
    for name in ('timed-reset-v1','timed-calibration-v1','timed-calibration-v2','r2-offline-v1'):
        run=HERE/'runs'/name;lock=batch.read(run/'evidence-lock.json')
        assert set(lock)=={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p!=run/'evidence-lock.json'}
        for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,(name,rel)
        report.append(dict(run=name,files=len(lock)))
    output=dict(status='PASS',r2_plan_sha256=batch.read(r2.RUN/'plan-lock.json')['sha256'],new_locks=report,new_real_model_calls=0,r1c_icarus=80,r2_offline_icarus=15)
    batch.atomic(HERE/'delivery-verification.json',output);print(json.dumps(output,indent=2))
if __name__=='__main__':main()
