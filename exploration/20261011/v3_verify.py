"""Read-only independent audit, new output only; no subprocess/model/simulation."""
import sys,json,hashlib,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];BASE=P/'r3-runner-v3'
sys.path[:0]=[str(BASE),str(ROOT),str(P/'r3')]
import runner,batch,rtl_lab as lab
spec=importlib.util.spec_from_file_location('transport_audit',BASE/'transport_acceptance_v2.py')
acceptance=importlib.util.module_from_spec(spec);spec.loader.exec_module(acceptance)
RUN=BASE/'runs/transport-v2';FIRST=BASE/'runs/transport-v1'
def lock(run):
    records=batch.read(run/'evidence-lock.json')
    assert set(records)=={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}
    for rel,h in records.items():assert lab.digest((run/rel).read_bytes())==h
    return len(records)
failed_files=lock(FIRST);transport_files=lock(RUN)
for rel,h in batch.read(FIRST/'source-lock.json').items():
    current=ROOT/rel
    if lab.digest(current.read_bytes())!=h:
        snapshot=FIRST/'source-snapshot'/current.name
        assert current.parent==BASE and snapshot.is_file() and lab.digest(snapshot.read_bytes())==h
assert batch.read(FIRST/'failure.json')['status']=='HARNESS_ERROR'
assert runner.hashes()==batch.read(RUN/'source-lock.json')
assert acceptance.historical()==batch.read(RUN/'preserved-before.json')
summary=batch.read(RUN/'summary.json');assert summary['status']=='PASS'
for row in summary['new_stdin']['records']+[summary['new_stdin']['mixed_stress']]:
    folder=RUN/'new-stdin/jobs'/row['id']/'call' if 'id' in row else RUN/'mixed-1MiB'
    data=(folder/'received-prompt.bin').read_bytes()
    assert data==(folder/'codex_prompt.txt').read_bytes()
    receipt=batch.read(folder/'receipt.json');config=batch.read(folder/'fixture-control.json')
    assert receipt['nonce']==config['nonce']==row['nonce']
    assert len(data)==receipt['bytes']==row['bytes']
    assert lab.digest(data)==receipt['sha256']==row['sha256']
    assert receipt['argv'][-1]=='-' and data.decode('utf-8') not in receipt['argv']
    if 'id' in row:
        original=P/'r3-runner-v2/runs/acceptance-v1/full-flow/jobs'/row['id']/'call/exact-prompt.txt'
        assert original.read_bytes()==data
        assert (folder/'exact-prompt.txt').read_bytes()==data
        assert batch.read(folder.parent/'generation.json')['status']=='GENERATED'
for p in (RUN/'original-argv').iterdir():
    result=batch.read(p/'transport-result.json')
    if result['status']=='CREATEPROCESS_ERROR':assert result['winerror']==206 and not (p/'receipt.json').exists()
    else:assert batch.read(p/'receipt.json')['sha256']==result['receipt_sha256']
for row in summary['negative']:
    result=batch.read(RUN/'negative'/row['mode']/'codex.json')
    assert result['returncode'] is not None
    if row['mode']=='timeout':assert result['timeout'] and result['killed']
    if row['mode']=='overflow':assert result['output_limit'] and result['killed']
    if row['mode']=='nonzero':assert result['returncode']==7
plan=runner.verify();assert not (runner.RUN/'jobs').exists()
reg=BASE/'runs/regression-v1';regsummary=batch.read(reg/'summary.json')
assert regsummary['real_model_calls']==0
if not (reg/'evidence-lock.json').exists():
    batch.atomic(reg/'evidence-lock.json',{str(p.relative_to(reg)):lab.digest(p.read_bytes()) for p in reg.rglob('*') if p.is_file()})
regfiles=lock(reg)
output=dict(status='PASS',real_model_calls=0,real_cli_generation_calls=0,simulator_calls=0,
    sources=len(runner.hashes()),preserved_bindings=len(acceptance.historical()),
    sealed_files=dict(failed_first=failed_files,transport=transport_files,regression=regfiles),
    byte_exact_branch_prompts=16,mixed_stress_bytes=summary['new_stdin']['mixed_stress']['bytes'],
    old_transport=summary['original_argv'],negative=summary['negative'],
    plan_sha256=batch.read(runner.RUN/'plan-lock.json')['sha256'],pending_slots=len(plan['jobs']),
    regression=regsummary,limit='Offline receiver only; real CLI stdin interface verified with local help; model/server context acceptance untested')
batch.atomic(P/'v3-verification.json',output);print(json.dumps(output,indent=2))
