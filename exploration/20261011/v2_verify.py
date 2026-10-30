"""Independent new-run bindings and prior evidence preservation audit."""
import sys,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE/'r3-runner-v2';OLD=HERE/'r3';ROOT=HERE.parents[1];sys.path[:0]=[str(BASE),str(OLD),str(ROOT)]
import runner,acceptance,batch,rtl_lab as lab
def main():
    plan=runner.verify();run=BASE/'runs/acceptance-v1';lock=batch.read(run/'evidence-lock.json')
    assert set(lock)=={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name not in ('run.lock','evidence-lock.json')}
    for rel,h in lock.items():assert lab.digest((run/rel).read_bytes())==h,rel
    for rel,h in batch.read(run/'source-lock.json').items():assert lab.digest((ROOT/rel).read_bytes())==h
    preserved=batch.read(run/'old-preservation-before.json');assert acceptance.preserved()==preserved
    full=run/'full-flow';fixture=batch.read(run/'fixture-plan.json');rows=batch.read(full/'results.json');summary=batch.read(full/'summary.json');receipts=0
    for job,row in zip(fixture['jobs'],rows):
        assert row['role']==job['role'] and row['pair']==job['pair'] and row['arm']==job['arm'] and 'stage' not in row
        assert row['judge']==batch.read(full/'jobs'/job['id']/'hidden-judge.json') and row['status']==row['judge']['status']
        folder=full/'jobs'/job['id'];assert lab.digest((folder/'response.txt').read_bytes())==row['generation']['response_sha256']
    for p in run.rglob('simulate.json'):
        process=batch.read(p);assert process['returncode']==0 and not process['timeout'] and not process['output_limit']
        command=process['command'];nonce=next(arg.split('=',1)[1] for arg in command if arg.startswith('+nonce='))
        m=re.fullmatch(r'RTL_LAB_V1 ([a-f0-9]+) checks=(\d+) errors=(\d+)',(p.parent/'verdict.txt').read_text().strip());assert m and m[1]==nonce;receipts+=1
    boundaries=batch.read(run/'boundary-results.json')
    for case in boundaries:
        payload=(run/(case['label']+'.txt')).read_bytes();assert len(payload)==case['bytes']
        assert case['result']['status']==('PASS' if len(payload)<=128*1024 else 'EXTRACTION_ERROR')
    derivation=batch.read(BASE/'derivation.json');assert lab.digest((OLD/'runner.py').read_bytes())==derivation['original_runner_sha256']
    assert lab.digest((OLD/'judge.py').read_bytes())==derivation['judge_copy_sha256']==lab.digest((BASE/'judge.py').read_bytes())
    loopback=batch.read(HERE/'v2-loopback-regression/summary.json');assert loopback['status']=='PASS'
    output=dict(status='PASS',real_model_calls=0,plan_sha256=batch.read(runner.RUN/'plan-lock.json')['sha256'],source_files=len(plan['source_hashes']),new_engineering_files=len(lock),prior_preserved_bindings=len(preserved),real_simulator_nonce_bindings=receipts,
                role_namespace_verified_rows=len(rows),boundary_sizes=[b['bytes'] for b in boundaries],first_fixture_statuses=summary['first_candidate_statuses'],paired_fixture_effects=summary['effects'],
                regression_original='34 tests; 2 skipped; 2 loopback methods failed (3 failures + 1 error)',regression_loopback_isolated=loopback,
                limitations='Engineering fixtures only. Original default-proxy regression failures retained; isolated loopback passes do not validate production transport or oversized model prompts.')
    batch.atomic(HERE/'v2-verification.json',output);print(json.dumps(output,indent=2))
if __name__=='__main__':main()
