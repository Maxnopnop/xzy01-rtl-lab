"""R4 new development mechanisms; procedural spec oracle, not derived from IR/RTL."""
import random,itertools
from pathlib import Path
BASE=Path(__file__).resolve().parent
TASKS={
'epoch_commit':dict(module='epoch_commit',inputs=[('write',1),('slot',1),('data',2),('commit',1),('abort_tx',1),('read_slot',1)],outputs=[('visible',2),('dirty',2),('committed',1)],seed=41001,
spec='Two-bank atomic staged transaction. Async active-low rst_n clears live and staged 2-bit bank values, both dirty bits and committed pulse. Every rising clk edge clears committed. abort_tx dominates commit and write: discard all staging, copy live values into staged banks, clear dirty, ignore write/commit. Otherwise first apply a write to staged[slot], marking that bank dirty; then if commit=1 atomically replace every dirty live bank with its staged value, including a write on this SAME edge, clear dirty and pulse committed even if no bank was dirty. Non-dirty live banks are unchanged. Staged banks persist after a commit and equal the corresponding new live values. Without commit/abort, staging never changes visible live values. visible is a combinational read of live[read_slot], forced zero during reset; dirty and committed are registered and hold between edges. Changes in write/slot/data/commit/abort while clk is stable must not mutate state. Inputs are unconstrained binary; repeated commits, abort with write+commit and repeated writes to one bank are defined.'),
'refund_credit':dict(module='refund_credit',inputs=[('submit',1),('refund',2),('cost',2)],outputs=[('credit',3),('accepted',1),('rejected',1),('can_pay',1)],seed=41002,
spec='Weighted credit ledger with capacity five. Async active-low rst_n clears 3-bit credit and accepted/rejected pulses. Every rising edge first form funded=min(5, old_credit + unsigned refund), regardless of submit. Clear accepted/rejected. If submit=1, cost=0 is invalid: rejected=1, keep funded. Else if funded>=cost consume cost and accepted=1; otherwise rejected=1 and keep funded. Without submit keep funded and both pulses zero; cost has no sequential effect. Thus same-edge refund can fund a purchase and saturation occurs BEFORE subtracting cost. credit and pulses hold between edges. can_pay is combinational: rst_n && cost!=0 && min(5,credit+refund)>=cost, forecasting the same rule using current credit; it may change as inputs change without a clock edge. Capacity arithmetic must not wrap at three or four bits. All binary input combinations are defined; reset dominates submit/refund.'),
'tagged_join':dict(module='tagged_join',inputs=[('av',1),('atag',1),('adata',2),('bv',1),('btag',1),('bdata',2),('flush',1)],outputs=[('pending_a',1),('pending_b',1),('joined',1),('result',2)],seed=41003,
spec='Two-channel tagged rendezvous with replacement before comparison. Async active-low rst_n clears cached-valid flags, cached tags/data, joined pulse and result. Each rising edge clears joined. flush=1 has priority: clear both caches/flags and result, ignore new samples. Otherwise independently replace channel A cache when av=1 and B cache when bv=1, setting its valid flag; no sample holds that cache. Then compare the UPDATED caches, including both newly sampled values on the same edge. If both valid and tags equal, joined=1, result=updated_A_data XOR updated_B_data, and clear both valid flags; keep the cached tag/data values until replaced or flush. Otherwise keep flags/caches and the old result. Thus incompatible tags can wait indefinitely, a newer sample supersedes an old matching sample BEFORE comparison, and consecutive matching pairs may join on consecutive edges. Invalid input tags/data have no effect. pending_a/pending_b report registered valid flags, all outputs hold between edges; reset dominates flush/samples. All binary inputs are defined.')}

def unpack(task,value):
    x={}
    for n,w in reversed(TASKS[task]['inputs']):x[n]=value&((1<<w)-1);value>>=w
    return x
def pack_input(task,**kwargs):
    value=0
    for n,w in TASKS[task]['inputs']:value=(value<<w)|kwargs.get(n,0)
    return value
def initial(task):
    if task=='epoch_commit':return dict(live=[0,0],staged=[0,0],mask=0,pulse=0)
    if task=='refund_credit':return dict(balance=0,accept=0,reject=0)
    return dict(a=None,b=None,pulse=0,result=0)
def step(task,s,x):
    if task=='epoch_commit':
        live=list(s['live']);staged=list(s['staged']);mask=s['mask'];pulse=0
        if x['abort_tx']:staged=list(live);mask=0
        else:
            if x['write']:staged[x['slot']]=x['data'];mask|=1<<x['slot']
            if x['commit']:
                for i in range(2):
                    if mask&(1<<i):live[i]=staged[i]
                mask=0;pulse=1
        return dict(live=live,staged=staged,mask=mask,pulse=pulse)
    if task=='refund_credit':
        balance=min(5,s['balance']+x['refund']);accept=reject=0
        if x['submit']:
            if x['cost'] and balance>=x['cost']:balance-=x['cost'];accept=1
            else:reject=1
        return dict(balance=balance,accept=accept,reject=reject)
    if x['flush']:return initial(task)
    a=(x['atag'],x['adata']) if x['av'] else s['a'];b=(x['btag'],x['bdata']) if x['bv'] else s['b'];pulse=0;result=s['result']
    if a is not None and b is not None and a[0]==b[0]:result=a[1]^b[1];a=b=None;pulse=1
    return dict(a=a,b=b,pulse=pulse,result=result)
def output(task,s,x,rst):
    if not rst:return 0
    if task=='epoch_commit':vals=[s['live'][x['read_slot']],s['mask'],s['pulse']]
    elif task=='refund_credit':vals=[s['balance'],s['accept'],s['reject'],int(x['cost']>0 and min(5,s['balance']+x['refund'])>=x['cost'])]
    else:vals=[int(s['a'] is not None),int(s['b'] is not None),s['pulse'],s['result']]
    value=0
    for v,(_,w) in zip(vals,TASKS[task]['outputs']):value=(value<<w)|v
    return value

# Hand-designed semantic witnesses, not generated from IR.
def sequences(task):
    p=lambda **x:pack_input(task,**x)
    if task=='epoch_commit':return [[p(write=1,data=3),p(read_slot=0),p(write=1,slot=1,data=2,commit=1),p(read_slot=1),p(write=1,data=1,commit=1,abort_tx=1),p(read_slot=0)],[p(write=1,data=2),p(write=1,data=1),p(commit=1),p(commit=1),p(abort_tx=1)]]
    if task=='refund_credit':return [[p(refund=3),p(refund=3,submit=1,cost=2),p(submit=1,cost=3),p(submit=1,cost=0),p(refund=2,submit=1,cost=2)],[p(refund=1,submit=1,cost=1),p(submit=1,cost=2),p(refund=3),p(refund=3),p(refund=3,submit=1,cost=3)]]
    return [[p(av=1,atag=0,adata=1),p(bv=1,btag=1,bdata=2),p(av=1,atag=1,adata=3),p(av=1,atag=0,adata=2,bv=1,btag=0,bdata=1),p(av=1,adata=3,bv=1,bdata=1,flush=1)],[p(av=1,atag=0,adata=1),p(av=1,atag=1,adata=2,bv=1,btag=0,bdata=3),p(bv=1,btag=1,bdata=1)]]
def vectors(task,seqs,mid=True):
    rows=[];s=initial(task);last=0;mask=(1<<sum(w for _,w in TASKS[task]['inputs']))-1
    def emit(clk,rst,value,kind):
        nonlocal s,last
        x=unpack(task,value)
        if not rst:s=initial(task)
        elif clk and not last:s=step(task,s,x)
        rows.append(dict(clk=clk,rst_n=rst,input=value,expected=output(task,s,x,rst),category=kind));last=clk
    for seq in seqs:
        emit(0,0,0,'reset');emit(1,0,mask,'reset_edge');emit(0,1,0,'release')
        for i,value in enumerate(seq):
            for clk,v,k in [(0,value,'pre'),(1,value,'edge'),(1,value^mask,'high_change'),(1,value,'restore'),(0,value,'fall')]:emit(clk,1,v,k)
            if mid and i==2:
                emit(0,0,value,'mid_reset');emit(0,1,value,'mid_release')
    return rows
def dataset(task):
    rng=random.Random(TASKS[task]['seed']);count=1<<sum(w for _,w in TASKS[task]['inputs'])
    public=vectors(task,sequences(task),False)
    extra=[[pack_input(task,refund=3),pack_input(task,refund=3),pack_input(task,submit=1,refund=3,cost=1)]] if task=='refund_credit' else []
    private=vectors(task,sequences(task)+extra+[[rng.randrange(count) for _ in range(24)] for _ in range(32)]+[[v,0,v] for v in range(count)],True)
    return public,private
