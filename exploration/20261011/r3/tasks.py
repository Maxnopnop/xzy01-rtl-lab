"""New temporal tasks: independent procedural oracle and hand-authored RTL."""
from pathlib import Path
import random,itertools
BASE=Path(__file__).resolve().parent
TASKS={
'cancel_deadline':dict(module='cancel_deadline',inputs=[('req',1),('cancel',1),('finish',1)],outputs=[('busy',1),('accepted',1),('completed',1),('cancelled',1),('expired',1)],seed=31001,
spec='A single outstanding request with a three-edge completion window. Async active-low rst_n clears all state and outputs. At each rising clk edge, clear accepted/completed/cancelled/expired pulses. If idle before the edge, req=1 accepts a request, sets busy=1 and remaining=3, pulses accepted. cancel/finish have no effect while idle, even on acceptance. If busy before the edge, ignore req. Priority is cancel, then finish, then deadline. cancel terminates with cancelled=1; else finish terminates with completed=1; else remaining=1 terminates with expired=1; otherwise decrement remaining. No replacement is accepted on any terminating edge. Thus after acceptance, the next three rising edges are the response window; finish or cancel at the third edge beats expiry. busy and pulses hold between edges; async reset dominates simultaneous events.'),
'retrigger_window':dict(module='retrigger_window',inputs=[('trigger',1),('tick',1),('enable',1),('length',2)],outputs=[('active',1),('remaining',2),('expired',1)],seed=31002,
spec='Retriggerable timer counting enabled tick edges. Async active-low rst_n clears active, remaining and expired. At every rising edge first clear the expired pulse. trigger has highest priority regardless of enable/tick and loads remaining=max(length,1), active=1, cancelling any old expiration. length is sampled only on trigger. Otherwise, if active and enable and tick, remaining=1 expires: active=0, remaining=0, expired=1; else decrement remaining. Without enabled tick retain timer state. An inactive timer ignores tick. Consecutive trigger edges restart the full interval. length=0 is defined to mean 1, not illegal. All outputs hold between edges; reset dominates all events.'),
'elastic_slot':dict(module='elastic_slot',inputs=[('in_valid',1),('out_ready',1),('in_data',2)],outputs=[('in_ready',1),('out_valid',1),('out_data',2)],seed=31003,
spec='One-entry elastic ready/valid buffer, no combinational data bypass. Async active-low rst_n clears occupancy and data. While reset is low force in_ready=0, out_valid=0 and out_data=0. Otherwise in_ready = !occupied || out_ready, out_valid=occupied, out_data=stored data (zero when empty). At a rising edge use pre-edge occupied and out_ready: if in_valid && in_ready, store in_data and set occupied=1, including simultaneous consume/replace. Else if occupied && out_ready, clear occupied and stored data=0. Else retain state. Empty input acceptance is visible only after its rising edge. Under occupied && !out_ready, out_data and out_valid hold despite arbitrary changes in in_valid/in_data. in_ready may change combinationally with out_ready; it is not a Moore hold output. Producer need not hold invalid data; input data on an accepted edge is authoritative. No output consumption happens while empty.'),
'rotating_owner':dict(module='rotating_owner',inputs=[('req0',1),('req1',1),('retire',1)],outputs=[('grant0',1),('grant1',1)],seed=31004,
spec='Two-client rotating ownership arbiter with registered one-hot grants. Async active-low rst_n clears both grants and initializes tie preference to client0. When idle before a rising edge, select a requesting client, breaking simultaneous requests by current preference. retire while idle is ignored. Once owned, hold that grant even if its request drops or the other client requests, until retire=1 at a rising edge. On retire set tie preference to the opposite of the retiring owner and immediately select among current req0/req1 using that new preference; if neither requests become idle. A retired owner can regain ownership when it is the sole requester. Preference persists through idle edges; it changes only on retire of a real owner. Both requesting with retire every edge must alternate owners after the first grant. Registered grants hold between edges; reset dominates retire and requests.')}

def unpack(task,value):
    out={}
    for name,width in reversed(TASKS[task]['inputs']):out[name]=value&((1<<width)-1);value>>=width
    return out

def initial(task):
    return {'busy':0,'left':0} if task=='cancel_deadline' else {'active':0,'remaining':0} if task=='retrigger_window' else {'full':0,'data':0} if task=='elastic_slot' else {'owner':-1,'preference':0}

def step(task,state,x):
    s=dict(state)
    if task=='cancel_deadline':
        pulses=dict(accepted=0,completed=0,cancelled=0,expired=0)
        if not s['busy']:
            if x['req']:s.update(busy=1,left=3);pulses['accepted']=1
        else:
            event='cancelled' if x['cancel'] else 'completed' if x['finish'] else 'expired' if s['left']==1 else None
            if event:s.update(busy=0,left=0);pulses[event]=1
            else:s['left']-=1
        s.update(pulses)
    elif task=='retrigger_window':
        s['expired']=0
        if x['trigger']:s.update(active=1,remaining=max(x['length'],1))
        elif s['active'] and x['enable'] and x['tick']:
            s['remaining']-=1
            if s['remaining']==0:s.update(active=0,expired=1)
    elif task=='elastic_slot':
        if x['in_valid'] and (not s['full'] or x['out_ready']):s.update(full=1,data=x['in_data'])
        elif s['full'] and x['out_ready']:s.update(full=0,data=0)
    else:
        if s['owner']!=-1 and not x['retire']:return s
        if s['owner']!=-1:s['preference']=1-s['owner']
        requests=[i for i in (0,1) if x['req'+str(i)]]
        s['owner']=s['preference'] if len(requests)==2 else requests[0] if requests else -1
    return s

def output(task,s,x,reset):
    if not reset:return 0
    if task=='cancel_deadline':vals=[s['busy']]+[s.get(k,0) for k in ('accepted','completed','cancelled','expired')]
    elif task=='retrigger_window':vals=[s['active'],s['remaining'],s.get('expired',0)]
    elif task=='elastic_slot':vals=[int(not s['full'] or x['out_ready']),s['full'],s['data']]
    else:vals=[int(s['owner']==0),int(s['owner']==1)]
    q=0
    for val,(_,width) in zip(vals,TASKS[task]['outputs']):q=(q<<width)|val
    return q

def vectors(task,sequences,mid_reset=False):
    rows=[];s=initial(task);last=0;width=sum(w for n,w in TASKS[task]['inputs']);mask=(1<<width)-1
    def emit(clk,rst,value,category):
        nonlocal s,last
        x=unpack(task,value)
        if not rst:s=initial(task)
        elif clk and not last:s=step(task,s,x)
        rows.append(dict(clk=clk,rst_n=rst,input=value,expected=output(task,s,x,rst),category=category));last=clk
    for seq in sequences:
        emit(0,0,0,'reset');emit(1,0,0,'reset_edge');emit(0,1,0,'retire')
        for i,value in enumerate(seq):
            emit(0,1,value,'pre');emit(1,1,value,'post');emit(1,1,value^mask,'high_input_change');emit(1,1,value,'restore');emit(0,1,value,'fall')
            if mid_reset and i%7==4:
                emit(i%2,0,value,'mid_reset');emit(i%2,0,value^mask,'reset_input_change');emit(i%2,1,value,'mid_retire');emit(0,1,value,'mid_fall')
    return rows

PUBLIC={
'cancel_deadline':[[4,0,0,0,4,3,4,1],[7,0,0,1,4,0,0,2],[4,4,4,4,4]],
'retrigger_window':[[19,8,8,12,12,12],[19,12,12,12],[19,31,12,12,12],[16,12,4,12],[18,4,4,12,12]],
'elastic_slot':[[9,10,11,5,15,4],[15,14,13,12,4],[9,5,11,7,4]],
'rotating_owner':[[6,7,7,7,7,0,1,6],[4,2,0,3,1,6],[2,0,1,6,7]]}

def dataset(task):
    width=sum(w for n,w in TASKS[task]['inputs']);count=1<<width;rng=random.Random(TASKS[task]['seed'])
    exhaustive=list(itertools.product(range(count),repeat=2))
    random_sequences=[[rng.randrange(count) for _ in range(24)] for _ in range(128)]
    return vectors(task,PUBLIC[task],True),vectors(task,exhaustive+random_sequences+PUBLIC[task],True)

def reference(task):return (BASE/'references'/f'{task}.sv').read_text(encoding='utf-8')
