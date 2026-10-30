"""Read-only R6 locks/receipts/expected values; no model or simulator replay."""
import json,sys
from pathlib import Path
import stream_process as s,tasks,reference_alt,intent,teacher,runner
from stage_categories import classify
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
def verify():
    failures=[];checked=0
    prior=s.read(BASE/'prior-lock.json')
    for rel,h in prior.items():
        p=ROOT/rel
        assert p.is_file() and s.digest(p.read_bytes())==h,rel
    for seal in sorted((BASE/'runs').rglob('evidence-lock.json')):
        for rel,h in s.read(seal).items():
            p=seal.parent/rel;assert p.is_file() and s.digest(p.read_bytes())==h,str(p);checked+=1
    for rel,h in s.read(BASE/'assets/lock.json').items():assert s.digest((BASE/'assets'/rel).read_bytes())==h
    stats={};judges=[]
    for task in tasks.TASKS:
        generated=tasks.datasets(task)
        stats[task]={}
        for name,fresh in zip(['public','private'],generated):
            rows=s.read(BASE/'assets'/(task+'-'+name+'.json'));assert rows==fresh
            values=[r['expected'] for r in rows];assert reference_alt.run(task,rows)==values
            result,irvalues=intent.check(teacher.make(task),'structured',task,rows);assert result['status']=='PASS' and irvalues==values
            stats[task][name]=len(rows)
        for filename in ['public-judge.json','private-judge.json','negative-judge.json']:
            folder=BASE/'runs/calibration-v1'/task;r=s.read(folder/filename)
            assert r['status']==('FUNCTION_FAIL' if filename.startswith('negative') else 'PASS')
            run=folder/('target-negative' if filename.startswith('negative') else filename.split('-')[0])
            assert s.read(run/'compile.json')['returncode']==0 and s.read(run/'simulate.json')['returncode']==0
            assert s.digest((run/'dut.sv').read_bytes())==r['rtl_sha256']
            assert s.digest((run/'testbench.sv').read_bytes())==r['tb_sha256']
            assert s.digest((run/'vectors.hex').read_bytes())==r['vectors_sha256']
            # Existing backend receipt binds its own nonce and exact check count.
            verdict=(run/'verdict.txt').read_text().strip().split()
            assert verdict[0]=='RTL_LAB_V1' and int(verdict[2].split('=')[1])==r['checks']
            judges.append(dict(task=task,status=r['status'],checks=r['checks'],nonce=verdict[1]))
    assert len({r['nonce'] for r in judges})==9
    cases=[(('PASS','PASS','PASS'),'ALL_MATCH'),(('FUNCTION_FAIL','FUNCTION_FAIL','PASS'),'IR_SPEC_DIVERGENCE_RTL_FOLLOWS_IR'),(('PASS','FUNCTION_FAIL','FUNCTION_FAIL'),'RTL_IMPLEMENTATION_DIVERGENCE'),(('FUNCTION_FAIL','PASS','FUNCTION_FAIL'),'RTL_CORRECT_DESPITE_IR_DIVERGENCE'),(('FUNCTION_FAIL','FUNCTION_FAIL','FUNCTION_FAIL'),'BOTH_DIVERGE_UNATTRIBUTED'),(('PASS','PASS','FUNCTION_FAIL'),'REFERENCE_OR_ALIGNMENT_CONFLICT'),(('UNSUPPORTED','PASS','NOT_ASSESSABLE'),'NOT_ASSESSABLE')]
    assert all(classify(*abc)==expected for abc,expected in cases)
    p=runner.verify();assert len(p['jobs'])==48 and not (runner.RUN/'dispatch-start.json').exists()
    assert not (runner.RUN/'jobs').exists()
    for j in p['jobs']:
        if 'prompt' in j:
            raw=(runner.RUN/'prompts'/j['id']/'prompt.txt').read_bytes();assert s.digest(raw)==j['prompt_sha256'] and raw.decode()==j['prompt']
    return dict(status='PASS',model_calls=0,plan_sha256=s.read(runner.RUN/'plan-lock.json')['sha256'],sources=len(p['source_hashes']),prior_bindings=len(prior),sealed_run_bindings=checked,
                actual_compile_calls=9,actual_simulate_calls=9,judges=judges,coverage_counts=stats,stage_classification_checks=7,
                untouched_plan_slots=48,required_default='34 tests / 3 failures / 1 error / 2 skips; retained without retry',descendant_cleanup='UNVERIFIED',fees='UNKNOWN',scope='Read-only hashes and pure references; no model or simulator replay')
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
