"""R6 original development tasks. Binary events, fixed small domains."""
import random
TASKS={
'ordered_retire':dict(module='ordered_retire',inputs=[('flush',1),('issue',1),('issue_tag',2),('finish',1),('finish_tag',2)],outputs=[('count',2),('retired',1),('retired_tag',2)],spec='Two-slot ordered retirement queue with distinct 2-bit tags. Async active-low reset clears all state and outputs. Only rising edges act. flush has priority: clear queue and retired_tag and retired pulse. Otherwise retired is one iff the OLD head exists and was already finished; retire that head and update retired_tag, else retired=0 and hold retired_tag. finish marks any OLD queued matching tag finished; unknown tags ignored, and a just-issued tag cannot finish on that same edge. issue appends unfinished issue_tag iff OLD count<2 and issue_tag differs from all OLD queued tags; otherwise ignored. A full OLD queue rejects issue even when retiring; an OLD duplicate rejects issue even if that tag retires. Accepted issue appends after survivors. count reflects occupied slots. Completion can occur out of order; retirement stays in order, at most one per edge. Falling edges and stable clock input/reset-release changes hold all outputs; reset assertion immediately clears at either clock level.'),
'restoring_divide':dict(module='restoring_divide',inputs=[('abort',1),('start',1),('advance',1),('numerator',4),('denominator',4)],outputs=[('busy',1),('done',1),('quotient',4),('remainder',4)],spec='Unsigned 4-bit restoring divider, rising edges only, async active-low reset zeroes all state/output. abort highest priority: busy=done=quotient=remainder=0 and discard work. Otherwise done is a one-edge pulse (default 0 each rising edge). When OLD busy=0, start accepts current numerator/denominator regardless advance: for denominator=0 finish immediately with busy=0,done=1,quotient=15,remainder=numerator; otherwise busy=1, load work, four accepted advance edges required, hold previous quotient/remainder. When OLD busy=1, start and operand changes ignored. advance=0 pauses all work and holds busy/quotient/remainder, done still clears. Each advance shifts next numerator MSB into partial remainder, shifts quotient, conditionally subtracts latched denominator and sets quotient low bit iff trial>=denominator. On the fourth advance publish new quotient/remainder, busy=0,done=1. A start simultaneous with that fourth advance is ignored (OLD busy). No implicit extra advance at acceptance. Falling/stable clock changes hold all output; reset assertion clears immediately, release alone does not act.'),
'tagged_join':dict(module='tagged_join',inputs=[('clear',1),('a_valid',1),('a_tag',2),('a_data',2),('b_valid',1),('b_tag',2),('b_data',2),('take',1)],outputs=[('a_full',1),('b_full',1),('out_valid',1),('out_tag',2),('out_data',4)],spec='Join two tagged streams with one holding slot per input and one output register. Async low reset clears all state. Rising edges only. clear highest priority clears every slot and output field. Otherwise decisions use OLD slots: capture A iff a_valid and OLD a_full=0; capture B iff b_valid and OLD b_full=0, retaining captured tag/data. If both OLD input slots full and tags unequal, discard the slot with smaller unsigned tag, even when output blocked. If both full and tags equal, move them to output only if OLD out_valid=0 or take=1; clear both input full flags and set out_valid=1,out_tag=old tag,out_data={old a_data,old b_data}. This replacement wins over take. If no move and take=1 clear out_valid but hold out_tag/out_data; ignored take on empty has same field-hold behavior. Input capture cannot replace a full OLD slot on its discard/move edge; newly captured slots are not compared until a later edge. Output blocked equal slots hold; unequal drop does not change output. All falling/stable clock changes hold all outputs; asynchronous reset immediate and release alone no update.')}
def unpack(task,value):
    x={}
    for n,w in reversed(TASKS[task]['inputs']):x[n]=value&((1<<w)-1);value>>=w
    return x
def pack_input(task,**x):
    value=0
    for n,w in TASKS[task]['inputs']:value=(value<<w)|x.get(n,0)
    return value
def initial(task):
    if task=='ordered_retire':return dict(q=[],retired=0,retired_tag=0)
    if task=='restoring_divide':return dict(busy=0,done=0,quotient=0,remainder=0,num=0,den=0,part=0,qwork=0,left=0)
    return dict(a_full=0,b_full=0,out_valid=0,out_tag=0,out_data=0,at=0,ad=0,bt=0,bd=0)
def step(task,state,x,edge):
    s={k:(list(v) if isinstance(v,list) else v) for k,v in state.items()}
    if not edge:return s
    if task=='ordered_retire':
        if x['flush']:return initial(task)
        q=s['q'];old=list(q);ret=bool(old and old[0][1]);s['retired']=int(ret)
        if ret:s['retired_tag']=old[0][0]
        q=[(tag,ready or (x['finish'] and tag==x['finish_tag'])) for tag,ready in old[int(ret):]]
        if x['issue'] and len(old)<2 and all(tag!=x['issue_tag'] for tag,ready in old):q.append((x['issue_tag'],False))
        s['q']=q
    elif task=='restoring_divide':
        if x['abort']:return initial(task)
        s['done']=0
        if not state['busy'] and x['start']:
            if not x['denominator']:s.update(busy=0,done=1,quotient=15,remainder=x['numerator'])
            else:s.update(busy=1,num=x['numerator'],den=x['denominator'],part=0,qwork=0,left=4)
        elif state['busy'] and x['advance']:
            trial=2*state['part']+(state['num']>>3);bit=int(trial>=state['den'])
            s.update(part=trial-bit*state['den'],qwork=(2*state['qwork']+bit)&15,num=(2*state['num'])&15,left=state['left']-1)
            if state['left']==1:s.update(busy=0,done=1,quotient=s['qwork'],remainder=s['part'])
    else:
        if x['clear']:return initial(task)
        if not state['a_full'] and x['a_valid']:s.update(a_full=1,at=x['a_tag'],ad=x['a_data'])
        if not state['b_full'] and x['b_valid']:s.update(b_full=1,bt=x['b_tag'],bd=x['b_data'])
        if state['a_full'] and state['b_full']:
            if state['at']<state['bt']:s['a_full']=0
            elif state['bt']<state['at']:s['b_full']=0
            elif not state['out_valid'] or x['take']:s.update(a_full=0,b_full=0,out_valid=1,out_tag=state['at'],out_data=4*state['ad']+state['bd']);return s
        if x['take']:s['out_valid']=0
    return s
def output(task,s):
    d=s|({'count':len(s['q'])} if task=='ordered_retire' else {})
    value=0
    for n,w in TASKS[task]['outputs']:value=(value<<w)|d[n]
    return value
def vectors(task,seqs,private=False):
    rows=[];s=initial(task);last=0
    def event(clk,rst,x,cat):
        nonlocal s,last
        if not rst:s=initial(task)
        else:s=step(task,s,unpack(task,x),clk==1 and last==0)
        rows.append(dict(clk=clk,rst_n=rst,input=x,expected=output(task,s),category=cat));last=clk
    for seq_index,seq in enumerate(seqs):
        event(0,0,0,'reset_low');event(0,1,0,'release_low')
        for i,x in enumerate(seq):
            event(0,1,x,'low_hold');event(1,1,x,'rising');event(1,1,x^1,'high_hold');event(0,1,x,'falling')
            if private and i in [2,7]:
                # Separate reset-interrupted paths, not the sole normal path.
                if i==7:event(1,1,x,'reset_before_high')
                event(last,0,x,'mid_reset');event(last,1,x,'stable_release')
        event(0,0,0,'end_reset')
    return rows
def datasets(task):
    if task=='ordered_retire':
        seq=[dict(issue=1,issue_tag=1),dict(issue=1,issue_tag=2),dict(finish=1,finish_tag=2),dict(finish=1,finish_tag=1),dict(issue=1,issue_tag=3),{},{}]
    elif task=='restoring_divide':
        seq=[dict(start=1,numerator=13,denominator=3),dict(advance=1),{},dict(advance=1),dict(advance=1),dict(start=1,advance=1,numerator=8,denominator=2),{}]
    else:seq=[dict(a_valid=1,a_tag=1,a_data=2),dict(b_valid=1,b_tag=1,b_data=3),{},dict(a_valid=1,a_tag=0,a_data=1,b_valid=1,b_tag=2,b_data=2),{},dict(a_valid=1,a_tag=2,a_data=1),{},dict(take=1)]
    public=vectors(task,[[pack_input(task,**x) for x in seq]])
    rng=random.Random(61011+list(TASKS).index(task));width=sum(w for n,w in TASKS[task]['inputs'])
    sequences=[[rng.randrange(1<<width) for _ in range(28)] for _ in range(12)]
    # Directed complete normal arithmetic paths, plus separate reset paths.
    if task=='restoring_divide':
        sequences += [[pack_input(task,start=1,numerator=n,denominator=d)]+[pack_input(task,advance=1)]*4+[0] for n in range(16) for d in range(16)]
    elif task=='ordered_retire':
        sequences += [[pack_input(task,issue=1,issue_tag=a),pack_input(task,issue=1,issue_tag=b),pack_input(task,finish=1,finish_tag=b),pack_input(task,finish=1,finish_tag=a),0,0,0] for a in range(4) for b in range(4)]
        sequences += [[pack_input(task,issue=1,issue_tag=1,finish=1,finish_tag=1),0,pack_input(task,issue=1,issue_tag=1,finish=1,finish_tag=1),pack_input(task,issue=1,issue_tag=1),0],
                      [pack_input(task,issue=1,issue_tag=1),pack_input(task,flush=1,issue=1,issue_tag=2,finish=1,finish_tag=1),0]]
    else:
        sequences += [[pack_input(task,a_valid=1,a_tag=a,a_data=2,b_valid=1,b_tag=b,b_data=1),0,pack_input(task,take=1),0] for a in range(4) for b in range(4)]
        sequences += [[pack_input(task,a_valid=1,a_tag=1,a_data=2,b_valid=1,b_tag=1,b_data=3),0,
                       pack_input(task,a_valid=1,a_tag=2,a_data=1,b_valid=1,b_tag=2,b_data=2),0,
                       pack_input(task,take=1),pack_input(task,clear=1,take=1,a_valid=1,b_valid=1),0]]
    if task=='restoring_divide':
        sequences += [[pack_input(task,start=1,numerator=15,denominator=2),pack_input(task,start=1,numerator=3,denominator=0),0,
                       pack_input(task,advance=1),pack_input(task,abort=1,start=1,advance=1,numerator=15,denominator=1),0],
                      [pack_input(task,start=1,numerator=13,denominator=3),pack_input(task,advance=1),0,pack_input(task,advance=1),pack_input(task,advance=1),pack_input(task,start=1,advance=1,numerator=8,denominator=2),0]]
    return public,vectors(task,sequences)+vectors(task,sequences[:12],True)
