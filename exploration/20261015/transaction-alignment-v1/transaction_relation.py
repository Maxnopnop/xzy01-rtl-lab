"""Proposed phase/offer/epoch relation; not executed during preparation."""
from collections import deque
from spec_checker import check
def strip(rows):return [{k:r[k] for k in ('cycle','rst','s','m')} for r in rows]
def ledger(rows):
 epoch=0;active=False;advance=False;q=[deque(),deque()];accepted=[];outputs=[[],[]];cancelled=[];unaccepted=[]
 for r in rows:
  if r['rst']:
   if active:
    cancelled.append(dict(epoch=epoch,pending=[[x['id'] for x in queue] for queue in q]))
    q=[deque(),deque()];active=False;advance=True
   continue
  if advance:epoch+=1;advance=False
  active=True;s=r['s']
  if s['valid']==s['ready']==1:
   token=dict(id=r['offer_id'],beat=[s['data'],s['last']],cycle=r['cycle']);accepted.append(token)
   for queue in q:queue.append(token)
  for i,m in enumerate(r['m']):
   if m['valid']==m['ready']==1:
    token=q[i].popleft() if q[i] else None
    outputs[i].append(dict(id=token['id'] if token else None,beat=[m['data'],m['last']],cycle=r['cycle'],source_cycle=token['cycle'] if token else None))
 return dict(accepted=accepted,outputs=outputs,cancelled=cancelled)
def assess(rows,plans):
 verdict=check(strip(rows),plans)
 if verdict['status']=='TRACE_INVALID':return dict(spec=verdict,ledger=None)
 # Driver offer ids must agree with independent per-epoch acceptance ordinal.
 positions={}
 for r in rows:
  if not r['rst'] and r['s']['valid']==r['s']['ready']==1:
   epoch,index=r['offer_id'];assert index==positions.get(epoch,0),'Driver ID mismatch';positions[epoch]=index+1
 book=ledger(rows)
 for epoch,plan in enumerate(plans):
  if plan['termination']=='reset':
   accepted_ids={tuple(x['id']) for x in book['accepted'] if x['id'][0]==epoch}
   book['cancelled'][epoch]['unaccepted']=[[epoch,i] for i in range(len(plan['beats'])) if (epoch,i) not in accepted_ids]
 return dict(spec=verdict,ledger=book)
def relation(ir,rtl):
 invalid={'TRACE_INVALID','INPUT_PROTOCOL_FAIL'}
 if ir['spec']['status'] in invalid or rtl['spec']['status'] in invalid:return dict(status='NOT_EVALUABLE',reason='Invalid sample or source environment')
 a,b=ir['ledger'],rtl['ledger']
 def ids(book):return [x['id'] for x in book['accepted']]
 if ids(a)!=ids(b) or a['cancelled']!=b['cancelled']:return dict(status='NOT_EVALUABLE',reason='Accepted or cancelled offer sets differ at fixed epoch boundaries')
 hard={'UNEXPECTED_TRANSACTION','BACKPRESSURE_FAIL','MISSING_TRANSACTION','LIVENESS_FAIL'}
 if any(hard.intersection(x['spec']['counts']) for x in (ir,rtl)):return dict(status='FUNCTION_FAIL',reason='Causality/hold/finite completion obligation violated')
 def transcript(book):return [[(x['id'],x['beat']) for x in sink] for sink in book['outputs']]
 return dict(status='PASS' if transcript(a)==transcript(b) else 'FUNCTION_FAIL',reason='Per-consumer identified transactions; timing may stutter')
