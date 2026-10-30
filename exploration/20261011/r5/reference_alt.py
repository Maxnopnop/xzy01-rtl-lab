"""Same author, different derivations: payload list fold and free-set distance minimum."""
import functools,operator
import tasks
def answers(task,rows):
    last=0;payload=None;escape=False;committed=[];busy=set();cursor=0;idx=0;sample=0;visible=0;pulse=valid=bad=0;result=[]
    for row in rows:
        x=tasks.unpack(task,row['input']);edge=row['clk']!=last
        if not row['rst_n']:
            payload=None;escape=False;committed=[];busy=set();cursor=idx=sample=visible=pulse=valid=bad=0
        elif edge:
            if task=='phase_snapshot':
                if row['clk']==0:sample=0 if x['clear_sample'] else x['data'] if x['capture'] else sample
                else:pulse=x['publish'];visible=sample if pulse else visible
            elif row['clk']==1 and task=='escape_frame':
                pulse=0
                if x['flush']:payload=None;escape=False
                elif x['feed']:
                    z=x['symbol']
                    if payload is None:
                        if z==0:payload=[];escape=False
                    elif escape:payload.append(z);escape=False
                    elif z==0:payload=[]
                    elif z==1:committed=list(payload);payload=None;pulse=1
                    elif z==2:escape=True
                    else:payload.append(z)
            elif row['clk']==1:
                valid=bad=0
                if x['free_req']:busy.discard(x['release_id'])
                if x['allocate']:
                    free=set(range(4))-busy
                    if free:idx=min(free,key=lambda k:(k-cursor)%4);busy.add(idx);cursor=(idx+1)%4;valid=1
                    else:bad=1
        if task=='phase_snapshot':s=dict(sampled=sample,visible=visible,published=pulse)
        elif task=='escape_frame':s=dict(active=int(payload is not None),escaped=int(escape),work_sum=functools.reduce(operator.xor,payload or [],0),work_count=len(payload or [])%4,last_sum=functools.reduce(operator.xor,committed,0),last_count=len(committed)%4,completed=pulse)
        else:s=dict(occupied=sum(1<<k for k in busy),hint=cursor,last_alloc=idx,alloc_valid=valid,rejected=bad)
        result.append(tasks.output(task,s));last=row['clk']
    return result
