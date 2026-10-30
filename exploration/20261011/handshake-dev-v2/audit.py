"""Read-only separately written temporal accounting; no checker or runner import."""
import hashlib,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];RUN=R/'calibration-v2'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(mapping,base):
 for name,h in mapping.items():
  p=Path(name) if Path(name).is_absolute() else base/name
  assert p.is_file() and sha(p)==h,name
def account(rows,episodes):
 # Indexed input history + consumption counters, not target deque code.
 epoch=0;was_active=False;advance=False;previous=None
 ins=[[] for _ in episodes];outs=[[[],[]] for _ in episodes];used=[[0,0] for _ in episodes];counts=Counter();aborted=[]
 for r in rows:
  if r['rst']:
   if was_active:
    assert episodes[epoch]['termination']=='reset'
    aborted.append(dict(epoch=epoch,cycle=r['cycle'],pending=[len(ins[epoch])-u for u in used[epoch]],unaccepted=len(episodes[epoch]['beats'])-len(ins[epoch])))
    was_active=False;advance=True
   previous=None;continue
  if advance:epoch+=1;advance=False
  was_active=True
  if previous:
   for n,(p,c) in enumerate(zip([previous['s']]+previous['m'],[r['s']]+r['m'])):
    if p['valid']==1 and p['ready']==0 and (c['valid']!=1 or (c['data'],c['last'])!=(p['data'],p['last'])):counts['INPUT_PROTOCOL_FAIL' if n==0 else 'BACKPRESSURE_FAIL']+=1
  s=r['s']
  if s['valid']==s['ready']==1:
   payload=[s['data'],s['last']];position=len(ins[epoch]);assert payload==episodes[epoch]['beats'][position]
   ins[epoch].append(dict(epoch=epoch,cycle=r['cycle'],beat=payload))
  for n,m in enumerate(r['m']):
   if m['valid']==m['ready']==1:
    payload=[m['data'],m['last']]
    if used[epoch][n]>=len(ins[epoch]):counts['UNEXPECTED_TRANSACTION']+=1
    else:
     if ins[epoch][used[epoch][n]]['beat']!=payload:counts['DATA_OR_ORDER_FAIL']+=1
     used[epoch][n]+=1
    outs[epoch][n].append(dict(epoch=epoch,cycle=r['cycle'],beat=payload))
  previous=r
 assert epoch==len(episodes)-1
 assert all(all(m['ready']==1 for m in r['m']) and not r['rst'] for r in rows[-8:])
 if len(ins[epoch])<len(episodes[epoch]['beats']):counts['LIVENESS_FAIL']+=1
 for n in range(2):
  if used[epoch][n]<len(ins[epoch]):counts['MISSING_TRANSACTION']+=1
 return dict(counts=dict(counts),aborted=aborted,accepted=[x for e in ins for x in e],delivered=[[x for e in outs for x in e[n]] for n in range(2)])
def main():
 prior=read(R/'prior-lock.json');verify(prior,ROOT)
 sources=read(RUN/'source-lock.json');verify(sources,R)
 evidence=read(RUN/'evidence-lock.json');verify(evidence,RUN)
 assert set(evidence)=={p.relative_to(RUN).as_posix() for p in RUN.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}
 assert sha(R/'checker.py')==sha(R.with_name('handshake-dev-v1')/'checker.py')
 summary=read(RUN/'summary.json');assert (summary['fixture_denominator'],summary['native_denominator'],summary['compile_count'],summary['sim_count'],summary['new_model_calls'])==(8,8,8,8,0)
 statuses=Counter();native_statuses=Counter();mismatches=[]
 for entry in summary['fixtures']:
  f=read(RUN/'fixtures'/entry['name']/'input.json');v=read(RUN/'fixtures'/entry['name']/'verdict.json')
  a=account(f['rows'],f['episodes'])
  for field in ['counts','aborted','accepted','delivered']:assert a[field]==v[field],(entry['name'],field)
  assert entry['matched'];statuses[v['status']]+=1
 for entry in summary['native']:
  folder=RUN/'rtl'/entry['name'];v=read(folder/'verdict.json');rows=read(folder/'normalized-trace.json');a=account(rows,entry['source_plan'])
  for field in ['counts','aborted','accepted','delivered']:assert a[field]==v[field],(entry['name'],field)
  assert len(rows)==80 and len(entry['commands'])==2
  for i,c in enumerate(entry['commands']):
   assert c['returncode']==0 and not c['timeout'] and sha(Path(c['argv'][0]))==c['executable_sha256']
   assert not (folder/f'{i}.stderr.bin').read_bytes()
  raw=(folder/'trace.txt').read_text().splitlines();assert len(raw)==80
  for line,r in zip(raw,rows):
   fields=line.split();assert len(fields)==14 and int(fields[0])==r['cycle'] and int(fields[1],2)==r['rst']
   for offset,e in zip([2,6,10],[r['s']]+r['m']):
    for j,(key,base) in enumerate([('valid',2),('ready',2),('data',16),('last',2)]):
     token=fields[offset+j];assert token==e[key] if isinstance(e[key],str) else int(token,base)==e[key]
  assert v['status']==entry['expected'];native_statuses[v['status']]+=1
  if not entry['matched']:mismatches.append(dict(name=entry['name'],declared=entry['expected_category'],actual=v['counts'],retained=True))
 assert not summary['all_expected'] and mismatches==[dict(name='shared_reset_stale',declared='DATA_OR_ORDER_FAIL',actual={'UNEXPECTED_TRANSACTION':1},retained=True)]
 for name,pending,unaccepted in [('shared_reset_flush',[0,1],2),('queue_reset_flush',[0,2],1)]:
  v=read(RUN/'rtl'/name/'verdict.json');assert v['aborted']==[dict(epoch=0,cycle=8,pending=pending,unaccepted=unaccepted)]
 early=read(RUN/'rtl/illegal_consume_before_accept/verdict.json')
 assert [x['beat'] for x in early['accepted']]==[x['beat'] for x in early['delivered'][0]]==[x['beat'] for x in early['delivered'][1]]
 assert early['accepted'][0]['cycle']==7 and all(o[0]['cycle']==3 for o in early['delivered'])
 presentation=read(RUN/'rtl/legal_valid_before_accept/normalized-trace.json')
 assert all(r['s']['valid']==1 and r['s']['ready']==0 and all(m['valid']==1 and m['ready']==0 for m in r['m']) for r in presentation[3:7])
 default=read(R.with_name('handshake-dev-v1')/'default-regression-v1/receipt.json');assert default['returncode']==1 and not default['timeout']
 assert sha(R.with_name('handshake-dev-v1')/'default-regression-v1/stderr.bin')==default['stderr_sha256']
 design=read(R/'semantic-examples.json');assert design['denominator']==len(design['examples'])==6
 packet_count=None
 if (R/'packet-lock.json').exists():
  packet=read(R/'packet-lock.json');verify(packet,R)
  excluded={'packet-lock.json','seal-verification.json','seal-audit.stdout.bin','seal-audit.stderr.bin'}
  actual={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
  assert set(packet)==actual;packet_count=len(packet)
 print(json.dumps(dict(status='PASS_INTEGRITY_AND_TEMPORAL_AUDIT_WITH_RETAINED_CALIBRATION_MISMATCH',prior_bindings=len(prior),sources=len(sources),evidence=len(evidence),packet_bindings=packet_count,fixtures=dict(statuses),native=dict(native_statuses),raw_events=640,calibration_exit=1,category_mismatches=mismatches,default_exit=1,default_rerun=False,model_calls=0,intent_design='DESIGN_ONLY_NOT_VERIFIED'),ensure_ascii=False))
if __name__=='__main__':main()
