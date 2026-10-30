"""Release candidate read-only audit, also checks untouched v1 preparation."""
import importlib.util,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(BASE))
import stream_process as s
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify():
    audit=load('r6_original_audit',BASE/'verify.py').verify()
    candidate=load('r6_candidate',Path(__file__).with_name('runner.py'));p=candidate.core.verify()
    assert len(p['jobs'])==len({j['id'] for j in p['jobs']})==48
    assert len(p['cases'])==6 and p['workers']==1 and p['retries']==0 and p['max_calls']==48
    assert not (candidate.core.RUN/'dispatch-start.json').exists() and not (candidate.core.RUN/'jobs').exists()
    for j in p['jobs']:
        if 'prompt' in j:assert s.digest((candidate.core.RUN/'prompts'/j['id']/'prompt.txt').read_bytes())==j['prompt_sha256']
    for r in audit['judges']:
        name='target-negative' if r['status']=='FUNCTION_FAIL' else ('public' if r['checks'] in [31,35] else 'private')
        folder=BASE/'runs/calibration-v1'/r['task']/name
        receipt=s.read(folder.parent/('negative-judge.json' if name=='target-negative' else name+'-judge.json'))
        process=s.read(folder/'simulate.json');assert '+nonce='+r['nonce'] in process['command'] and receipt['receipt_nonce']==r['nonce']
        errors=int((folder/'verdict.txt').read_text().split()[3].split('=')[1]);assert (errors>0)==(r['status']=='FUNCTION_FAIL')
    live=[]
    for startfile in (BASE/'runs').rglob('process-start.json'):
        start=s.read(startfile)
        if start['identity'] is not None and s.identity(start['pid'])==start['identity']:live.append(str(startfile))
    assert not live,'Owned fixture children still active'
    total=sum(x.stat().st_size for x in BASE.rglob('*') if x.is_file())
    assert total<750*1024**2
    stderr=(BASE/'runs/required-default-v1/stderr.log').read_text(errors='replace')
    assert 'Ran 34 tests' in stderr and 'FAILED (failures=3, errors=1, skipped=2)' in stderr
    return audit|dict(plan_sha256=s.read(candidate.core.RUN/'plan-lock.json')['sha256'],candidate='engineering-v2/runner.py',sources=len(p['source_hashes']),
                      v1_plan_preserved=s.read(BASE/'runs/prepared-v1/plan-lock.json')['sha256'],job_binding_checks=4,
                      calibration_event_checks=sum(r['checks'] for r in audit['judges']),owned_children_alive=live,preparation_disk_bytes=total,
                      counts_scope='9 compile/sim are dedicated new calibration; required regression EDA subprocesses not aggregated as research checks',
                      actual_compile_calls=None,actual_simulate_calls=None,calibration_compile_calls=9,calibration_simulate_calls=9)
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
