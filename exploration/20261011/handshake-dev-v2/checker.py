"""Development-only per-consumer transaction checker; no DUT golden waveform."""
from collections import Counter,deque

class BadTrace(ValueError): pass

def bit(x):
    if type(x) is not int or x not in (0,1): raise BadTrace('Nonbinary control')
    return x

def beat(x):
    if not isinstance(x,(tuple,list)) or len(x)!=2: raise BadTrace('Beat shape')
    data,last=x
    if type(data) is not int or not 0<=data<=255: raise BadTrace('Valid payload not binary8')
    return data,bit(last)

def endpoint(x):
    if not isinstance(x,dict) or set(x)!={'valid','ready','data','last'}: raise BadTrace('Endpoint shape')
    valid,ready=bit(x['valid']),bit(x['ready'])
    # Invalid fields do not participate in semantics, including X/Z.
    payload=beat([x['data'],x['last']]) if valid else None
    return valid,ready,payload

def check(rows,episodes,*,consumers=2,drain_cycles=8,max_cycles=256):
    """Rows sampled immediately BEFORE each rising edge; explicit finite horizon."""
    errors=[];counts=Counter();q=[deque() for _ in range(consumers)]
    guards=[None]*(consumers+1);accepted=[];delivered=[[] for _ in range(consumers)]
    aborted=[];plans=[];seen=[0]*len(episodes);epoch=0;active=False;reset_pending=False
    def fail(category,cycle,**detail):
        counts[category]+=1
        if len(errors)<8: errors.append(dict(category=category,cycle=cycle,epoch=epoch,**detail))
    try:
        if consumers!=2 or type(drain_cycles) is not int or not 1<=drain_cycles<=64:raise BadTrace('Development domain')
        if not isinstance(rows,list) or not 1<=len(rows)<=max_cycles:raise BadTrace('Trace length')
        if not isinstance(episodes,list) or not episodes:raise BadTrace('Missing independent source plan')
        for episode in episodes:
            if not isinstance(episode,dict) or set(episode)!={'beats','termination'} or episode['termination'] not in ('reset','drain'):raise BadTrace('Episode shape')
            if not isinstance(episode['beats'],list) or len(episode['beats'])>64:raise BadTrace('Plan length')
            plans.append([beat(x) for x in episode['beats']])
        if episodes[-1]['termination']!='drain':raise BadTrace('Final epoch must drain')
        prior_cycle=-1;fair_tail=0
        for row in rows:
            if not isinstance(row,dict) or set(row)!={'cycle','rst','s','m'}:raise BadTrace('Row shape')
            cycle=row['cycle']
            if type(cycle) is not int or cycle!=prior_cycle+1:raise BadTrace('Missing/duplicate cycle')
            prior_cycle=cycle;rst=bit(row['rst'])
            if not isinstance(row['m'],list) or len(row['m'])!=consumers:raise BadTrace('Consumer count')
            if rst:
                fair_tail=0
                if active:
                    if episodes[epoch]['termination']!='reset':raise BadTrace('Unplanned reset can hide loss')
                    aborted.append(dict(epoch=epoch,cycle=cycle,pending=[len(x) for x in q],unaccepted=len(plans[epoch])-seen[epoch]))
                    q=[deque() for _ in range(consumers)];guards=[None]*(consumers+1)
                    active=False;reset_pending=True
                continue
            s=endpoint(row['s']);ms=[endpoint(x) for x in row['m']]
            if reset_pending:
                epoch+=1;reset_pending=False
            if epoch>=len(episodes):raise BadTrace('Unexpected reset epoch')
            active=True
            fair_tail=fair_tail+1 if all(x[1] for x in ms) else 0
            for index,(valid,ready,payload) in enumerate([s]+ms):
                if guards[index] is not None and (not valid or payload!=guards[index]):
                    fail('INPUT_PROTOCOL_FAIL' if index==0 else 'BACKPRESSURE_FAIL',cycle,endpoint='source' if index==0 else f'consumer{index-1}',expected=list(guards[index]),observed=list(payload) if payload is not None else None,valid=valid)
                guards[index]=payload if valid and not ready else None
            # Ordering permits a zero-cycle combinational input->output handshake.
            if s[0] and s[1]:
                position=seen[epoch]
                if position>=len(plans[epoch]) or s[2]!=plans[epoch][position]:
                    fail('INPUT_PROTOCOL_FAIL',cycle,endpoint='source_plan',position=position,expected=list(plans[epoch][position]) if position<len(plans[epoch]) else None,observed=list(s[2]))
                seen[epoch]+=1;accepted.append(dict(epoch=epoch,cycle=cycle,beat=list(s[2])))
                for queue in q:queue.append((s[2],cycle))
            for index,(valid,ready,payload) in enumerate(ms):
                if valid and ready:
                    if not q[index]:
                        fail('UNEXPECTED_TRANSACTION',cycle,consumer=index,observed=list(payload))
                    else:
                        expected,origin=q[index].popleft()
                        if payload!=expected:fail('DATA_OR_ORDER_FAIL',cycle,consumer=index,source_cycle=origin,expected=list(expected),observed=list(payload))
                    delivered[index].append(dict(epoch=epoch,cycle=cycle,beat=list(payload)))
        if not active or epoch!=len(episodes)-1:raise BadTrace('Trace truncated before final epoch')
        if fair_tail<drain_cycles:raise BadTrace('Insufficient declared fair-ready tail')
        if seen[epoch]<len(plans[epoch]):fail('LIVENESS_FAIL',prior_cycle,reason='source_plan_not_accepted',remaining=len(plans[epoch])-seen[epoch])
        for index,queue in enumerate(q):
            if queue:fail('MISSING_TRANSACTION',prior_cycle,consumer=index,remaining=len(queue),first_expected=list(queue[0][0]),source_cycle=queue[0][1])
        status='INPUT_PROTOCOL_FAIL' if counts['INPUT_PROTOCOL_FAIL'] else ('FUNCTION_FAIL' if counts else 'PASS')
        return dict(status=status,counts=dict(counts),errors=errors,cycles=len(rows),accepted=accepted,delivered=delivered,aborted=aborted,pending=[len(x) for x in q],source_accepted_per_epoch=seen,assessment='not_scored' if status=='INPUT_PROTOCOL_FAIL' else 'finite_contract',latency='Variable; bounded by declared trace/drain, not exact reference cycles')
    except (BadTrace,TypeError,KeyError) as e:
        return dict(status='TRACE_INVALID',assessment='not_scored',message=str(e),counts=dict(counts),errors=errors,accepted=accepted,delivered=delivered,aborted=aborted)
