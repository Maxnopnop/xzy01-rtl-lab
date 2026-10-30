"""At most8 original-reference alias compile/sim pairs; first anomaly stops."""
import time,json
from pathlib import Path
import core
P=Path(__file__).resolve().parent
def main():
    plan=core.read(P/'calibration-plan.json');assert core.sha(P/'source-lock.json')==plan['source_lock_sha256'] and core.sha(P/'input-lock.json')==plan['input_lock_sha256']
    assert all(core.sha(P/k)==h for k,h in core.read(P/'source-lock.json').items())
    assert all(core.sha(k)==h for k,h in core.read(P/'input-lock.json').items())
    root=P/'calibration';root.mkdir(exist_ok=False);start=time.monotonic();rows=[]
    core.save(root/'start.json',{'utc':core.utc(),'plan_sha256':core.sha(P/'calibration-plan.json'),'model_calls':0})
    for task in plan['tasks']:
        if time.monotonic()-start>300 or core.size(root)>67108864-8388608:break
        info=plan['aliases'][task];assert core.sha(P/info['path'])==info['sha256']
        folder=root/task;folder.mkdir();verdict=core.judge({'task':task},folder,(P/info['path']).read_bytes().decode())
        verdict.update(task=task,kind='REFERENCE_ALIAS_HARNESS_ONLY',independent_oracle=False);core.save(folder/'assessment.json',verdict);rows.append(verdict)
        print(json.dumps({'task':task,'status':verdict['status'],'receipt':verdict.get('receipt')}),flush=True)
        if verdict['status']!='REFERENCE_PASS':break
    summary={'utc':core.utc(),'passed':len(rows)==8 and all(r['status']=='REFERENCE_PASS' for r in rows),'compile_attempts':sum((root/t/'compile-started.json').exists() for t in plan['tasks']),'sim_attempts':sum((root/t/'simulate-started.json').exists() for t in plan['tasks']),'rows':rows,'not_started':plan['tasks'][len(rows):],'source_lock_sha256':plan['source_lock_sha256'],'input_lock_sha256':plan['input_lock_sha256'],'model_calls':0,'independent_oracle':False}
    core.save(root/'summary.json',summary);core.save(root/'evidence-lock.json',{p.relative_to(root).as_posix():core.sha(p) for p in sorted(root.rglob('*')) if p.is_file()})
    return 0 if summary['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
