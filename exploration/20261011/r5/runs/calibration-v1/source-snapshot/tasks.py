"""R5 observable specs and incremental oracle, no IR/RTL converter dependency."""
import random,itertools
TASKS={
'phase_snapshot':dict(module='phase_snapshot',inputs=[('capture',1),('clear_sample',1),('data',2),('publish',1)],outputs=[('sampled',2),('visible',2),('published',1)],seed=51001,spec='Two-phase snapshot. Async active-low rst_n clears sampled, visible and published. Only FALLING clk edges update sampled: clear_sample has priority and sets sampled=0; else capture=1 samples unsigned 2-bit data; else hold. Only RISING clk edges update visible and published: published=publish, and publish=1 copies the previously captured sampled into visible; publish=0 holds visible. capture/clear_sample/data have no effect on a rising edge and publish has no effect on a falling edge. sampled is exposed directly; all three outputs hold while clk remains at either level, independent of input changes. Reset assertion and release at stable high or low are defined: assertion clears immediately, release alone must not update anything. All binary inputs defined.'),
'escape_frame':dict(module='escape_frame',inputs=[('feed',1),('symbol',2),('flush',1)],outputs=[('active',1),('escaped',1),('work_sum',2),('work_count',2),('last_sum',2),('last_count',2),('completed',1)],seed=51002,spec='Escaped token frame parser on rising clk edges, async active-low reset clears every output. Tokens: 0 START, 1 END, 2 ESC, 3 DATA. Every rising edge clears completed. flush dominates feed: abort active frame, clear active/escaped/work_sum/work_count, preserve last_sum/last_count. Else feed=0 holds every other output, including escaped. Outside a frame only fed START opens a frame with zero work_sum/work_count and escaped=0. In an active frame, if escaped=1, ANY fed symbol is literal payload (even START/END/ESC), XOR its unsigned value into work_sum, increment work_count modulo four, clear escaped. Otherwise START restarts work_sum/work_count at zero; END commits work_sum/work_count to last_sum/last_count, pulses completed, clears active/escaped and work outputs; ESC sets escaped without consuming payload; DATA adds literal 3 by XOR and modulo-four count. Commit preserves last results until another commit or reset. Exposed work and active outputs hold between rising edges; falling edges and input-only changes have no effect. All binary inputs defined.'),
'masked_ring_alloc':dict(module='masked_ring_alloc',inputs=[('release',1),('release_id',2),('allocate',1)],outputs=[('occupied',4),('hint',2),('last_alloc',2),('alloc_valid',1),('rejected',1)],seed=51003,spec='Four-resource rotating bitmap allocator on rising edges. Async active-low reset clears occupied bitmap, hint, last_alloc, alloc_valid and rejected. Every rising edge clears alloc_valid/rejected. First release=1 clears occupied[release_id], including an already free resource. Then allocate=1 selects the first free resource in cyclic order hint, hint+1, hint+2, hint+3 modulo four, using the AFTER-release bitmap. If a resource exists, set its occupied bit, set last_alloc to selected index, hint=(selected+1) modulo four, and alloc_valid=1. If none exists, rejected=1 and keep hint/last_alloc. Without allocation keep hint/last_alloc; release still applies. Full bitmap simultaneous release+allocation succeeds by reallocating the released resource. Arbitrary releases and sparse holes are allowed, not FIFO. All outputs registered and hold through falling edges and input changes. All binary inputs defined.')}
def unpack(task,value):
    d={}
    for n,w in reversed(TASKS[task]['inputs']):d[n]=value&((1<<w)-1);value>>=w
    return d
def pack_input(task,**x):
    v=0
    for n,w in TASKS[task]['inputs']:v=(v<<w)|x.get(n,0)
    return v
def initial(task):return {n:0 for n,w in TASKS[task]['outputs']}
def step(task,s,x,edge):
    t=dict(s)
    if task=='phase_snapshot':
        if edge==0:
            if x['clear_sample']:t['sampled']=0
            elif x['capture']:t['sampled']=x['data']
        else:
            t['published']=x['publish']
            if x['publish']:t['visible']=s['sampled']
    elif edge==1 and task=='escape_frame':
        t['completed']=0
        if x['flush']:t.update(active=0,escaped=0,work_sum=0,work_count=0)
        elif x['feed']:
            z=x['symbol']
            if not s['active']:
                if z==0:t.update(active=1,escaped=0,work_sum=0,work_count=0)
            elif s['escaped']:t.update(escaped=0,work_sum=s['work_sum']^z,work_count=(s['work_count']+1)%4)
            elif z==0:t.update(work_sum=0,work_count=0)
            elif z==1:t.update(active=0,escaped=0,work_sum=0,work_count=0,last_sum=s['work_sum'],last_count=s['work_count'],completed=1)
            elif z==2:t['escaped']=1
            else:t.update(work_sum=s['work_sum']^z,work_count=(s['work_count']+1)%4)
    elif edge==1:
        t.update(alloc_valid=0,rejected=0)
        mask=s['occupied']&~(1<<x['release_id']) if x['release'] else s['occupied']
        if x['allocate']:
            chosen=next((i for j in range(4) if not mask&(1<<(i:=(s['hint']+j)%4))),None)
            if chosen is None:t['rejected']=1
            else:mask|=1<<chosen;t.update(hint=(chosen+1)%4,last_alloc=chosen,alloc_valid=1)
        t['occupied']=mask
    return t
def output(task,s):
    v=0
    for n,w in TASKS[task]['outputs']:v=(v<<w)|s[n]
    return v
def sequences(task):
    p=lambda **x:pack_input(task,**x)
    if task=='phase_snapshot':return [[(p(publish=1,data=2),p(capture=1,data=3)),(p(publish=1,data=1),p(capture=1,clear_sample=1,data=2)),(p(publish=1,clear_sample=1),p(capture=1,data=2)),(p(publish=0,capture=1,data=1),p())]]
    if task=='escape_frame':return [[(p(feed=1,symbol=z),0) for z in [0,2,1,3,1,0,3,0,3,1]],[(p(feed=1,symbol=0),0),(p(feed=1,symbol=2),0),(p(feed=0,symbol=1),0),(p(feed=1,symbol=0),0),(p(feed=1,symbol=1),0),(p(feed=1,symbol=0),0),(p(feed=1,symbol=3,flush=1),0)]]
    return [[(p(allocate=1),0)]*4+[(p(allocate=1),0),(p(release=1,release_id=2,allocate=1),0),(p(release=1,release_id=0),0),(p(allocate=1),0)]]
def vectors(task,seqs,private=False):
    rows=[];s=initial(task);last=0;bits=sum(w for _,w in TASKS[task]['inputs']);mask=(1<<bits)-1
    def emit(clk,rst,value,kind):
        nonlocal s,last
        if not rst:s=initial(task)
        elif clk!=last:s=step(task,s,unpack(task,value),clk)
        rows.append(dict(clk=clk,rst_n=rst,input=value,expected=output(task,s),category=kind));last=clk
    for seq in seqs:
        emit(0,0,0,'reset_low');emit(0,1,0,'release_low')
        for i,(rise,fall) in enumerate(seq):
            emit(0,1,rise,'low_pre');emit(1,1,rise,'rising')
            if private:
                for b in range(bits):emit(1,1,rise^(1<<b),'high_hold_bit');emit(1,1,rise,'high_restore')
            else:emit(1,1,rise^mask,'high_hold');emit(1,1,rise,'high_restore')
            if private and i==2:
                emit(1,0,mask,'midreset_high');emit(1,1,rise,'release_high_no_edge')
            emit(0,1,fall,'falling')
            if private:
                for b in range(bits):emit(0,1,fall^(1<<b),'low_hold_bit');emit(0,1,fall,'low_restore')
            else:emit(0,1,fall^mask,'low_hold');emit(0,1,fall,'low_restore')
            if private and i==5:emit(0,0,mask,'midreset_low');emit(0,1,fall,'release_low_no_edge')
    return rows
def datasets(task):
    seqs=sequences(task);r=random.Random(TASKS[task]['seed']);count=1<<sum(w for _,w in TASKS[task]['inputs'])
    hidden=seqs+[[ (r.randrange(count),r.randrange(count)) for _ in range(24)] for _ in range(12)]+[[(v,0),(0,v),(v,v)] for v in range(count)]
    return vectors(task,seqs),vectors(task,hidden,True)
