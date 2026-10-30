"""Independent receipts, anchor expectations and old-evidence read-only audit."""
import sys,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE/'r3';ROOT=HERE.parents[1];sys.path[:0]=[str(BASE),str(ROOT)]
import tasks,runner,batch,rtl_lab as lab

def main():
    plan=runner.verify();locks=[];receipts=0;compiles=0
    for name in ('calibration-v1','control-tests-v1'):
        run=BASE/'runs'/name;lock=batch.read(run/'evidence-lock.json')
        assert set(lock)=={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')}
        for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,(name,rel)
        for rel,h in batch.read(run/'source-lock.json').items():assert lab.digest((ROOT/rel).read_bytes())==h,rel
        locks.append(dict(run=name,files=len(lock)))
    results=batch.read(BASE/'runs/calibration-v1/results.json')
    for row in results:
        for split in ('public','private'):
            r=row[split];folder=BASE/'runs/calibration-v1'/row['label']/split;c=batch.read(folder/'compile.json');compiles+=1
            assert not c['timeout'] and not c['output_limit']
            if r['status']=='COMPILE_FAIL':assert c['returncode']!=0;continue
            assert c['returncode']==0
            s=batch.read(folder/'simulate.json');assert s['returncode']==0 and not s['timeout'] and not s['output_limit']
            match=re.fullmatch(r'RTL_LAB_V1 ([a-f0-9]+) checks=(\d+) errors=(\d+)',(folder/'verdict.txt').read_text().strip())
            assert match and match[1]==r['receipt_nonce'] and int(match[2])==r['checks']
            assert (int(match[3])==0)==(r['status']=='PASS');receipts+=1
            assert lab.digest((folder/'testbench.sv').read_bytes())==r['tb_sha256']
            assert lab.digest((folder/'vectors.hex').read_bytes())==r['vectors_sha256']
    anchors={'cancel_deadline':([4,0,0,0],[24,16,16,1]),'retrigger_window':([19,12,12,12],[14,12,10,1]),'elastic_slot':([9,10,5],[5,5,8]),'rotating_owner':([6,7,7,7],[2,1,2,1])}
    for task,(inputs,expected) in anchors.items():assert [r['expected'] for r in tasks.vectors(task,[inputs]) if r['category']=='post']==expected
    old=[]
    for name in ('compound-v1','delayed-v1','factorial20-v1','formal-v1','r1b-v1','r1b-v2','timed-reset-v1','timed-calibration-v1','timed-calibration-v2','r2-prepared-v1'):
        run=HERE/'runs'/name;lock=batch.read(run/'evidence-lock.json')
        for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,(name,rel)
        for rel,h in batch.read(run/'plan.json')['source_hashes'].items():assert lab.digest((ROOT/rel).read_bytes())==h,rel
        old.append(dict(run=name,files=len(lock)))
    assets=batch.read(runner.ASSETS/'lock.json')
    for rel,h in assets.items():assert lab.digest((runner.ASSETS/rel).read_bytes())==h
    output=dict(status='PASS',model_calls=0,planned_unique_calls=24,shared_first_calls=8,branch_calls=16,plan_sha256=batch.read(runner.RUN/'plan-lock.json')['sha256'],new_locks=locks,
                compile_checks=compiles,simulator_receipts=receipts,manual_semantic_anchors=anchors,old_locks=old,old_files=sum(x['files'] for x in old),
                task_event_counts={t:{s:len(batch.read(runner.ASSETS/(t+'-'+s+'.json'))) for s in ('public','private')} for t in tasks.TASKS},
                limits='Manual anchors are a few independent concrete traces; bounded calibration does not prove all semantic correctness.')
    batch.atomic(HERE/'r3-verification.json',output);print(json.dumps(output,indent=2))
if __name__=='__main__':main()
