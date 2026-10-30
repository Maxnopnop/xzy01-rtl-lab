"""Read-only packet/source/prior integrity and bounded evidence audit; no subprocess."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
counts={}
for name,base in [('prior-lock.json',ROOT),('method-lock.json',ROOT),('packet-lock.json',R)]:
 p=R/name
 if not p.exists():
  assert name=='packet-lock.json','Missing required lock'
  continue
 d=read(p)
 for n,h in d.items():
  file=Path(n) if Path(n).is_absolute() else base/n
  assert file.is_file() and sha(file)==h,n
 counts[name]=len(d)
 if name=='packet-lock.json':
  excluded={'packet-lock.json','seal-verification.json','seal-audit.stdout.bin','seal-audit.stderr.bin'}
  actual={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts}
  assert actual==set(d),'Packet file set changed'
sources=read(R/'SOURCE_MANIFEST.json');access=read(R/'source-access.json')
assert len({x['url'] for x in access})==len(access),'Repeated source URL attempt'
for row in sources['files']:
 p=R/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
 assert any(a['url']==row['url'] and a.get('sha256')==row['sha256'] and a['status']==200 for a in access)
assert len(sources['files'])==sources['file_count']==31
assert sum(x['bytes'] for x in sources['files'])==sources['total_bytes']<=8*1024*1024
assert {str(p.relative_to(R)) for p in (R/'upstream').rglob('*') if p.is_file()}=={x['path'] for x in sources['files']}
cases=read(R/'candidates.json');decision=read(R/'preparation-decision.json')
assert [c['candidate'] for c in cases]==list(range(1,13))
assert not any(c['eligible'] or c['project_model_calls'] or c['method_tuned_on_candidate'] for c in cases)
assert decision['candidate_denominator']==12 and decision['eligible']==0 and decision['jobs']==[] and decision['model_calls']==decision['reserved_calls']==0 and decision['execution_plan_sha256'] is None
adapt=read(R/'access-adaptation.json');assert not adapt['method_changes'] and not adapt['production_reference_diff'] and adapt['model_requests']==0
for x in read(R/'history-inventory.json'):assert sha(ROOT/x['path'])==x['sha256'],x['path']
receipt=read(R/'source-calibration-v1/receipts.json');assert receipt['new_model_calls']==0 and len(receipt['receipts'])==2
for row in receipt['receipts']:
 folder=R/'source-calibration-v1'/row['name']
 assert sha(folder/'tb.v')==row['tb_sha256']
 assert len(row['commands'])==2 and all(x['returncode']==0 and not x['timeout'] for x in row['commands'])
 assert all((folder/f'{i}.{stream}.bin').is_file() for i in range(2) for stream in ['stdout','stderr'])
 cmd=row['commands'][0]['argv'];assert sha(Path(cmd[-2]))==row['source_sha256']
out=(R/'source-calibration-v1/broadcast_invalid_payload/1.stdout.bin').read_text()
assert 'original=5a5a valid=0' in out and 'payload_hold=1' in out and 'valid_cleared=1 payload_not_contract_zero=a7a7' in out
out=(R/'source-calibration-v1/stat_counter_singlebeat/1.stdout.bin').read_text()
assert 'snapshot_bytes=1 snapshot_frames=0' in out and 'TRANSFER data=00 last=1' in out
assert not any((R/n).exists() for n in ['runs','assets','plan.json']), 'Unexpected executable assets'
print(json.dumps(dict(status='PASS_NEGATIVE_PREPARATION_INTEGRITY',bindings=counts,source_files=sources['file_count'],source_bytes=sources['total_bytes'],candidate_denominator=12,eligible=0,compile=2,simulate=2,original_test_suites_executed=0,model_calls=0,reserved=0,execution_plan_sha256=None,source_403=sum(x['status']==403 for x in access),source_404=sum(x['status']==404 for x in access),writes=0,meaning='Integrity checks pass; execution/reference/coverage eligibility gate failed, not model or method performance.')))
