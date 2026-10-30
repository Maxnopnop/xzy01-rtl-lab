"""Read-only integrity and independent transaction ledger audit, no subprocess."""
import hashlib,json
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lock(p,base):
 d=read(p)
 for n,h in d.items():
  file=Path(n) if Path(n).is_absolute() else base/n
  assert file.is_file() and sha(file)==h,n
 return len(d)
def ledger(rows):
 # Separate flat transcript abstraction: no checker import or expected queue.
 epoch=0;active=False;advance=False;inputs={};outputs={};holds=Counter()
 previous=None
 for row in rows:
  if row['rst']:
   if active:active=False;advance=True
   previous=None;continue
  if advance:epoch+=1;advance=False
  active=True
  inputs.setdefault(epoch,[]);outputs.setdefault(epoch,[[],[]])
  if previous is not None:
   for i,(before,after) in enumerate(zip([previous['s']]+previous['m'],[row['s']]+row['m'])):
    if before['valid']==1 and before['ready']==0:
     if after['valid']!=1 or (after['data'],after['last'])!=(before['data'],before['last']):holds['source' if i==0 else 'sink']+=1
  s=row['s']
  if s['valid']==s['ready']==1:inputs[epoch].append([s['data'],s['last']])
  for i,m in enumerate(row['m']):
   if m['valid']==m['ready']==1:outputs[epoch][i].append([m['data'],m['last']])
  previous=row
 return inputs,outputs,holds
prior=lock(R/'prior-lock.json',ROOT)
run=R/'calibration-v1';source_count=lock(run/'source-lock.json',R);run_count=lock(run/'evidence-lock.json',run)
assert {str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}==set(read(run/'evidence-lock.json'))
s=read(run/'summary.json');assert (s['fixture_denominator'],s['rtl_denominator'],s['tool_compile'],s['tool_simulate'],s['new_model_calls'])==(22,10,10,10,0)
assert s['all_expected_outcomes'] and all(x['matched'] for x in s['trace_fixtures']+s['rtl'])
positive=negative=0
for entry in s['trace_fixtures']:
 folder=run/'fixtures'/entry['name'];f=read(folder/'input.json');v=read(folder/'result.json')
 assert v['status']==f['expected_status']
 inputs,outputs,holds=ledger(f['rows'])
 if v['status']=='PASS':
  positive+=1;assert not holds
  for epoch,plan in enumerate(f['episodes']):
   if plan['termination']=='drain':assert inputs[epoch]==plan['beats'] and all(o==plan['beats'] for o in outputs[epoch])
   else:assert inputs[epoch]==plan['beats'][:len(inputs[epoch])] and all(o==inputs[epoch][:len(o)] for o in outputs[epoch])
 elif v['status']=='FUNCTION_FAIL':
  negative+=1;category=f['expected_category'];assert category in v['counts']
  if category=='BACKPRESSURE_FAIL':assert holds['sink']>0
  if category=='LIVENESS_FAIL':assert len(inputs[0])<len(f['episodes'][0]['beats'])
  if category in ['DATA_OR_ORDER_FAIL','MISSING_TRANSACTION','UNEXPECTED_TRANSACTION']:assert any(o!=inputs[epoch] for epoch,oo in outputs.items() for o in oo)
for row in s['rtl']:
 folder=run/'rtl'/row['name'];v=read(folder/'verdict.json');trace=read(folder/'normalized-trace.json')
 assert len(trace)==80 and len(row['commands'])==2 and all(x['returncode']==0 and not x['timeout'] for x in row['commands'])
 raw=(folder/'trace.txt').read_text().splitlines();assert len(raw)==len(trace)
 for line,event in zip(raw,trace):
  words=line.split();assert len(words)==14 and int(words[0])==event['cycle'] and int(words[1],2)==event['rst']
  for offset,endpoint in zip([2,6,10],[event['s']]+event['m']):
   for j,(field,base) in enumerate([('valid',2),('ready',2),('data',16),('last',2)]):
    value=endpoint[field];token=words[offset+j]
    assert (int(token,base)==value if type(value) is int else token.lower()==value.lower()),'Raw/normalized sampling mismatch'
 for c in row['commands']:assert sha(Path(c['argv'][0]))==c['executable_sha256']
 assert b'HANDSHAKE_DEV_TRACE rows=80' in (folder/'1.stdout.bin').read_bytes()
 inputs,outputs,holds=ledger(trace)
 if row['expected_status']=='PASS':
  assert not holds and inputs[0]==s['source_plan'][0]['beats'] and all(o==inputs[0] for o in outputs[0])
 else:
  cat=row['expected_category'];assert cat in v['counts']
  if cat=='BACKPRESSURE_FAIL':assert holds['sink']>0
  elif cat=='LIVENESS_FAIL':assert len(inputs[0])<5
  else:assert any(o!=inputs[0] for o in outputs[0])
reg=read(R/'default-regression-v1/receipt.json')
assert not reg['timeout'],'Default regression timed out; unresolved infrastructure failure'
assert sha(R/'default-regression-v1/stdout.bin')==reg['stdout_sha256'] and sha(R/'default-regression-v1/stderr.bin')==reg['stderr_sha256']
for n,h in reg['source_sha256'].items():assert sha(ROOT/n)==h
unit=read(R/'unit-v1/receipt.json');assert unit['returncode']==0
for n,h in unit['sources'].items():assert sha(R/n)==h
packet_count=None
if (R/'packet-lock.json').exists():
 packet_count=lock(R/'packet-lock.json',R)
 excluded={'packet-lock.json','seal-verification.json','seal-audit.stdout.bin','seal-audit.stderr.bin'}
 assert {str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and str(p.relative_to(R)) not in excluded and '__pycache__' not in p.parts}==set(read(R/'packet-lock.json'))
print(json.dumps(dict(status='PASS_DEVELOPMENT_CALIBRATION_AUDIT',prior_bindings=prior,source_bindings=source_count,calibration_bindings=run_count,packet_bindings=packet_count,fixtures=22,fixture_status_counts=dict(Counter(x['observed'] for x in s['trace_fixtures'])),native_configurations=10,native_pass=3,native_faults_detected=7,native_compile=10,native_simulate=10,default_regression_exit=reg['returncode'],new_model_calls=0,r7_packet_sha256=sha(ROOT/'exploration/20261011/r7/packet-lock.json'),independent_cross_check='Flat per-epoch input/output transcripts and adjacent stalled-sender checks, not imported checker or DUT waveform golden',writes=0,limitation='Synthetic same-author development and finite traces; no external heldout/model efficacy/production integration/unbounded proof')))
