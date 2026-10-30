"""Independent preparation audit; no generation/simulation and no old artifact writes."""
import sys,json,re,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];BASE=P/'r4';V3=P/'r3-runner-v3'
sys.path[:0]=[str(BASE),str(ROOT)]
import runner_v2 as runner,tasks,intent,calibration_contracts as contracts,batch,rtl_lab as lab
def seal_check(run):
    lock=batch.read(run/'evidence-lock.json');actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')}
    assert set(lock)==actual,(run,len(lock),len(actual))
    for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,(run,rel)
    return len(lock)
def source_check(run):
    lock=run/'source-lock.json'
    if not lock.exists():return
    for rel,h in batch.read(lock).items():
        if lab.digest((ROOT/rel).read_bytes())!=h:
            snapshot=run/'source-snapshot'/rel
            assert snapshot.is_file() and lab.digest(snapshot.read_bytes())==h,(run,rel)
def prior():
    spec=importlib.util.spec_from_file_location('v3_prior_audit',V3/'transport_acceptance_v2.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    records=module.historical()
    for p in V3.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:records[str(p.relative_to(ROOT))]=lab.digest(p.read_bytes())
    for run in (V3/'runs/transport-v1',V3/'runs/transport-v2',V3/'runs/regression-v1'):seal_check(run)
    prep=batch.read(V3/'runs/prepared-v3/plan.json')
    for rel,h in prep['source_hashes'].items():assert lab.digest((ROOT/rel).read_bytes())==h
    assert not (V3/'runs/prepared-v3/jobs').exists()
    return records
def main():
    p=runner.verify();assert not (runner.RUN/'jobs').exists()
    records=prior();batch.atomic(BASE/'prior-bindings.json',records)
    assert len(p['jobs'])==48 and len(p['cases'])==6
    assert sum(j['role']=='intent' for j in p['jobs'])==12 and sum(j['role']=='first_rtl' for j in p['jobs'])==12 and sum(j['role']=='branch' for j in p['jobs'])==24
    for rel,h in batch.read(BASE/'assets-v1/lock.json').items():assert lab.digest((BASE/'assets-v1'/rel).read_bytes())==h
    events={}
    for t in tasks.TASKS:
        pub,private=tasks.dataset(t);assert batch.read(BASE/'assets-v1'/(t+'-public.json'))==pub;assert batch.read(BASE/'assets-v1'/(t+'-private.json'))==private
        events[t]=dict(public=len(pub),private=len(private))
        for rep in ('structured','linear'):
            raw=intent.serialize(contracts.contract(t),rep);parsed=intent.parse(raw,rep,t)
            assert intent.run(parsed,t,private)==[r['expected'] for r in private]
    reg=BASE/'runs/regression-v1'
    if not (reg/'evidence-lock.json').exists():runner.seal(reg)
    sealed={};compile_count=0;receipts=0
    for name in ('calibration-v1','calibration-v2','calibration-v3','calibration-v4','control-v1','unknown-v2','regression-v1'):
        run=BASE/'runs'/name;sealed[name]=seal_check(run);source_check(run)
        compile_count+=len(list(run.rglob('compile.json')))
        for sp in run.rglob('simulate.json'):
            result=batch.read(sp);receipt=(sp.parent/'verdict.txt').read_text(encoding='utf-8').strip()
            m=re.fullmatch(r'RTL_LAB_V1 ([0-9a-f]+) checks=(\d+) errors=(\d+)',receipt)
            assert m and '+nonce='+m[1] in result['command'] and result['returncode']==0 and not result['timeout']
            receipts+=1
    control=BASE/'runs/control-v1';seal_check(control/'full-flow')
    rows=batch.read(control/'full-flow/results.json');jobs=batch.read(control/'fixture-plan.json')['jobs']
    for row,job in zip(rows,jobs):
        assert all(row[k]==job[k] for k in ('id','case','task','role','representation','arm')) and 'stage' not in row
        folder=control/'full-flow/jobs'/row['id'];raw=(folder/'response.txt').read_bytes();assert lab.digest(raw)==row['generation']['response_sha256']
        if row['role']!='intent':assert set(row['judge'])=={'intent_spec','rtl_spec','rtl_intent'}
    cs=batch.read(control/'summary.json');assert cs['status']=='PASS' and cs['real_model_calls']==0
    unknown=batch.read(BASE/'runs/unknown-v2/unknown/summary.json');assert unknown['started']==1 and unknown['statuses']==dict(UNKNOWN_INTERRUPTED=1,PENDING=47)
    for case in p['cases']:
        js=[j for j in p['jobs'] if j['case']==case['id'] and j['role']=='intent'];assert js[0]['prompt'].split('Produce an implementation')[0]==js[1]['prompt'].split('Produce an implementation')[0]
        assert all(j['prompt_sha256']==lab.digest(j['prompt'].encode()) for j in js)
    for rel,h in batch.read(BASE/'templates/lock.json').items():assert lab.digest((BASE/'templates'/rel).read_bytes())==h
    output=dict(status='PASS',real_model_calls=0,pending_unique_calls=48,plan_sha256=batch.read(runner.RUN/'plan-lock.json')['sha256'],source_files=len(p['source_hashes']),prior_bindings=len(records),sealed_run_files=sealed,retained_compile_evaluations=compile_count,retained_simulator_nonce_bindings=receipts,events=events,role_rows_verified=48,model_intent_rows=0,offline_mock_calls=49,unknown_reserved=1,regression=batch.read(reg/'summary.json'),limitations='Counts are retained R4 artifacts excluding repository regression temporary fixtures; artificial contracts/mock outputs are not model scores; server context/strict token equality/descendant process-tree cleanup unverified')
    batch.atomic(BASE/'verification.json',output);print(json.dumps(output,indent=2))
if __name__=='__main__':main()
