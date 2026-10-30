"""Read-only raw receipt/asset/plan audit; no model or simulator calls."""
import json,re,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path[:0]=[str(BASE),str(ROOT)]
import tasks,reference_alt,intent,teacher,runner
lab=runner.lab;batch=runner.batch
def seal_check(run):
    records=batch.read(run/'evidence-lock.json');actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')}
    assert actual==set(records),(run,len(actual),len(records))
    for rel,h in records.items():assert lab.digest((run/rel).read_bytes())==h,(run,rel)
    return len(records)
def main():
    p=runner.verify();assert not (runner.RUN/'jobs').exists();assert len({j['id'] for j in p['jobs']})==48
    assert [j['role'] for j in p['jobs'][:4]].count('branch')==0
    for c in p['cases']:
        js=[j for j in p['jobs'] if j['case']==c['id']];assert len(js)==8
        for j in js:
            if j['role']=='branch':assert j['first_id'].endswith('__second' if j['representation']=='direct' else '__first')
            if 'prompt' in j:
                assert j['prompt_sha256']==lab.digest(j['prompt'].encode())
                if j['representation']=='direct':assert 'next_rising' not in j['prompt'] and 'r_occupied' not in j['prompt'] and 'references/' not in j['prompt']
    prior=batch.read(BASE.parent/'r4/prior-bindings.json')
    for rel,h in prior.items():assert lab.digest((ROOT/rel).read_bytes())==h,rel
    old=BASE.parent/'r4';oldfiles=0
    for run in (old/'runs').iterdir():
        if run.is_dir() and (run/'evidence-lock.json').exists():oldfiles+=seal_check(run)
    for rel,h in batch.read(old/'runs/prepared-v2/plan.json')['source_hashes'].items():assert lab.digest((ROOT/rel).read_bytes())==h,rel
    sealed={run.name:seal_check(run) for run in (BASE/'runs').iterdir() if run.is_dir() and (run/'evidence-lock.json').exists()}
    sourcechecks=0
    for lock in (BASE/'runs').glob('*/source-lock.json'):
        for rel,h in batch.read(lock).items():
            candidates=[ROOT/rel,lock.parent/'source-snapshot'/Path(rel).name]
            assert any(c.is_file() and lab.digest(c.read_bytes())==h for c in candidates),(lock,rel)
            sourcechecks+=1
    simulations=[];compiles=[]
    for file in (BASE/'runs').rglob('compile.json'):
        r=batch.read(file);compiles.append(dict(path=str(file.relative_to(BASE)),returncode=r['returncode']))
    for file in (BASE/'runs').rglob('simulate.json'):
        r=batch.read(file);assert r['returncode']==0 and not r['timeout'] and not r['output_limit'];nonce=next(x.split('=',1)[1] for x in r['command'] if x.startswith('+nonce='))
        receipt=(file.parent/'verdict.txt').read_text().strip();m=re.fullmatch(r'RTL_LAB_V1 (\w+) checks=(\d+) errors=(\d+)',receipt);assert m and m[1]==nonce
        assert int(m[2])==len((file.parent/'vectors.hex').read_text().splitlines())
        simulations.append(dict(path=str(file.relative_to(BASE)),nonce=nonce,checks=int(m[2]),errors=int(m[3])))
    assets={}
    for t in tasks.TASKS:
        for split,rows in zip(('public','private'),tasks.datasets(t)):
            assert batch.read(runner.ASSETS/f'{t}-{split}.json')==rows
            assert reference_alt.answers(t,rows)==[r['expected'] for r in rows]
            assert intent.check(json.dumps(teacher.contract(t)),'structured',t,rows)[0]['status']=='PASS'
            assets[t+'-'+split]=len(rows)
    result=dict(status='PASS',real_model_calls=0,model_slots_started=0,pending_slots=48,source_files=len(p['source_hashes']),source_bindings_checked=sourcechecks,sealed_files=sealed,preserved_prior_bindings=len(prior),preserved_r4_sealed_files=oldfiles,compile_calls=len(compiles),simulate_calls=len(simulations),assets=assets,plan_sha256=batch.read(runner.RUN/'plan-lock.json')['sha256'],regression=batch.read(BASE/'runs/regression-v1/summary.json'),scope='Offline preparation only; same-author references; no old RTL replay')
    batch.atomic(BASE/'audit-receipts.json',dict(compiles=compiles,simulations=simulations));batch.atomic(BASE/'verification.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
