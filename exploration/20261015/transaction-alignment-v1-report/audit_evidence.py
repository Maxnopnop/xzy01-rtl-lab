"""Post-run read-only evidence accounting, no target imports or subprocesses."""
import hashlib,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];P=R.with_name('transaction-alignment-v1');RUN=P/'run-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def unpack_raw(path):
 out=[]
 for i,line in enumerate(path.read_text().splitlines()):
  t=line.split();assert len(t)==16 and int(t[0])==i//2 and t[1]==('PRE' if i%2==0 else 'POST')
  def number(x,b):return x if any(c in x.lower() for c in 'xz') else int(x,b)
  ports=[dict(zip(('valid','ready','data','last'),[number(t[j],b) for j,b in zip(range(k,k+4),(2,2,16,2))])) for k in (4,8,12)]
  out.append(dict(cycle=int(t[0]),phase=t[1],rst=1-int(t[2],2),offer_index=int(t[3]),s=ports[0],m=ports[1:]))
 assert len(out)==160;return out
def plans(scene):
 if scene in (0,4):return [[[17,0],[18,0],[19,1]],[[161,0],[162,0],[163,1]]]
 return [[[32+i,int(i==7)] for i in range(8)]] if scene==1 else [[[81,1]]] if scene in (2,3) else [[[17,0],[18,0],[19,1]]]
def temporal(rows,scene):
 # Flat histories and count of already matched deliveries; compare source time.
 ins=[];outs=[[],[]];aborted=[];errors=Counter();epoch=0;active=False;advance=False;previous=None;used=[0,0];current=[]
 pp=plans(scene)
 for r in rows:
  if r['rst']:
   if active:
    aborted.append(dict(epoch=epoch,cycle=r['cycle'],pending=[len(current)-n for n in used],unaccepted=len(pp[epoch])-len(current)))
    active=False;advance=True
   previous=None;continue
  if advance:epoch+=1;advance=False;current=[];used=[0,0]
  active=True
  if previous:
   for n,(a,b) in enumerate(zip([previous['s']]+previous['m'],[r['s']]+r['m'])):
    if a['valid']==1 and a['ready']==0 and (b['valid']!=1 or (a['data'],a['last'])!=(b['data'],b['last'])):errors['INPUT_PROTOCOL_FAIL' if n==0 else 'BACKPRESSURE_FAIL']+=1
  s=r['s']
  if s['valid']==s['ready']==1:
   assert [s['data'],s['last']]==pp[epoch][len(current)]
   event=dict(epoch=epoch,cycle=r['cycle'],beat=[s['data'],s['last']]);current.append(event);ins.append(event)
  for n,m in enumerate(r['m']):
   if m['valid']==m['ready']==1:
    payload=[m['data'],m['last']]
    if used[n]==len(current):errors['UNEXPECTED_TRANSACTION']+=1
    else:
     if current[used[n]]['beat']!=payload:errors['DATA_OR_ORDER_FAIL']+=1
     assert current[used[n]]['cycle']<=r['cycle'];used[n]+=1
    outs[n].append(dict(epoch=epoch,cycle=r['cycle'],beat=payload))
  previous=r
 assert epoch==len(pp)-1
 assert all(not r['rst'] and all(m['ready']==1 for m in r['m']) for r in rows[-8:])
 if len(current)<len(pp[epoch]):errors['LIVENESS_FAIL']+=1
 for n in used:
  if n<len(current):errors['MISSING_TRANSACTION']+=1
 return dict(counts=dict(errors),accepted=ins,delivered=outs,aborted=aborted)
def main():
 assert not (R/'audit.json').exists(),'No overwrite of audit evidence'
 plan=read(P/'plan.json');summary=read(RUN/'summary.json');digest=sha(P/'plan.json')
 assert digest==read(P/'plan-lock.json')['sha256']=='c2aeef0482f72c1deded6bf45d6aae6012a889dc4f71801a633e4aa04e942c10'
 for n,h in plan['source_hashes'].items():assert sha(P/n)==h,n
 prior=read(P/'prior-lock.json')
 for n,h in prior.items():assert sha(ROOT/n)==h,n
 evidence=read(RUN/'evidence-lock.json')
 for n,h in evidence.items():assert sha(RUN/n)==h,n
 assert set(evidence)=={p.relative_to(RUN).as_posix() for p in RUN.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}
 assert summary['status']=='COMPLETED_EXPECTATIONS_MATCHED' and summary['pending']==[] and summary['actual_calls']==dict(ir=11,compile=11,sim=11)
 observed_axes={key:Counter() for key in ('ir_spec','rtl_spec','intent')};descriptor_axes={key:Counter() for key in observed_axes};checks=[];calls=Counter();phase_events=0
 for case,row in zip(plan['cases'],summary['results']):
  folder=RUN/case['id'];assert row['id']==case['id'] and row['matched'] and row['observed']==case['expected']
  for key,value in row['observed'].items():(observed_axes if row['executed'] else descriptor_axes)[key][value]+=1
  if not row['executed']:
   assert case['id']=='10_reset_policy_missing' and not list(folder.glob('*receipt.json'))
   checks.append(dict(id=case['id'],kind='PREDECLARED_NOT_RUN_NOT_TOOL_OBSERVATION'));continue
  for name in ('ir','compile','sim'):
   receipt=read(folder/(name+'-receipt.json'));started=read(folder/(name+'-started.json'))
   assert receipt['returncode']==0 and not receipt['timeout'] and receipt['argv']==started['argv'] and receipt['reserved']
   assert sha(Path(receipt['argv'][0]))==receipt['executable_sha256']
   assert not (folder/(name+'.stderr.bin')).read_bytes();calls[name]+=1
  raw=unpack_raw(folder/'trace.txt');assert raw==read(folder/'native-normalized-events.json')
  full=read(folder/'native-pre-full.json');assert len(full)==80
  for a,b in zip(raw[::2],full):
   assert all(a[k]==b[k] for k in ('cycle','rst','s','m')) and b['offer_id']==[int(case['scene'] in (0,4) and a['cycle']>=8),a['offer_index']]
  ir_events=read(folder/'ir-events.json');ir_rows=read(folder/'ir-pre.json');assert len(ir_events)==160 and len(ir_rows)==80
  ports=[('s_ready',1),('m_valid0',1),('m_data0',8),('m_last0',1),('m_valid1',1),('m_data1',8),('m_last1',1)]
  for i,e in enumerate(ir_events):
   assert e['cycle']==i//2 and e['phase']==('PRE' if i%2==0 else 'POST') and e['input_event']['clk']==i%2
   packed=0
   for n,w in ports:packed=(packed<<w)|e['outputs'][n]
   assert packed==e['packed_output']
  for name,rows in [('ir',ir_rows),('rtl',full)]:
   derived=temporal(rows,case['scene']);v=read(folder/(name+'-assessment.json'))['spec']
   if name=='rtl' and case.get('drop_rtl_cycle') is not None:
    view=read(folder/'native-assessment-view.json');assert len(view)==79 and [r['cycle'] for r in view]==[i for i in range(80) if i!=6] and v['status']=='TRACE_INVALID';assert not derived['counts']
   else:
    for field in ('counts','accepted','delivered','aborted'):assert derived[field]==v[field],(case['id'],name,field)
  if case['id'] in ('01_same_mapping','07_partial_delivery_reset'):
   assert read(folder/'same-mapping-phase-identity.json')==dict(compared_events=160,differences=[])
   for a,b in zip(ir_events,raw):
    o=a['outputs'];assert o['s_ready']==b['s']['ready']
    for n,m in enumerate(b['m']):assert [o[f'm_{key}{n}'] for key in ('valid','data','last')]==[m[key] for key in ('valid','data','last')]
   phase_events+=160
  checks.append(dict(id=case['id'],kind='RAW_HASH_TEMPORAL_ACCOUNTING',native_events=160,ir_events=160))
 early=read(RUN/'06_early_consume_flat_equal/rtl-assessment.json')['spec']
 assert early['accepted'][0]['cycle']==7 and all(s[0]['cycle']==3 for s in early['delivered'])
 assert all([x['beat'] for x in s]==[x['beat'] for x in early['accepted']] for s in early['delivered'])
 gap=RUN/'09_reset_acceptance_gap'
 assert read(gap/'ir-assessment.json')['spec']['aborted'][0]['pending']==[0,1] and read(gap/'rtl-assessment.json')['spec']['aborted'][0]['pending']==[0,2]
 assert read(gap/'intent-assessment.json')['status']=='NOT_EVALUABLE'
 save(R/'audit.json',dict(status='PASS_READ_ONLY_EVIDENCE_HASH_AND_TEMPORAL_ACCOUNTING',plan_sha256=digest,source_bindings=len(plan['source_hashes']),prior_bindings=len(prior),run_bindings=len(evidence),executed_pairs=11,not_run_descriptors=1,executed_axes={k:dict(v) for k,v in observed_axes.items()},not_run_predeclared_axes={k:dict(v) for k,v in descriptor_axes.items()},actual_processes=dict(calls),native_events=1760,ir_events=1760,phase_identity_events=phase_events,checks=checks,new_ir_or_tool_runs=0,model_calls=0,scope='Same-author read-only post-run audit, not coordinator independent review or original batch-run equivalence proof'))
 print(json.dumps(read(R/'audit.json'),ensure_ascii=False))
if __name__=='__main__':main()
