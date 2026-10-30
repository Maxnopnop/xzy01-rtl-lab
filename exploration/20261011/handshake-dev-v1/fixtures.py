"""Hand-authored development witnesses, independent schedules, no golden RTL."""
from copy import deepcopy
A=(0x12,0);B=(0xe4,1)
def port(valid=0,ready=1,payload=(0,0)):
    return dict(valid=valid,ready=ready,data=payload[0],last=payload[1])
def empty(n=24):return [dict(cycle=i,rst=0,s=port(),m=[port(),port()]) for i in range(n)]
PLAN=[dict(beats=[list(A),list(B)],termination='drain')]
def base(delay=0):
    rows=empty()
    rows[0]['s']=port(1,1,A);rows[1]['s']=port(1,1,B)
    for sink,events in [(0,[(1,0,A),(2,1,A),(3,0,B),(4,1,B)]),(1,[(2,0,A),(3,1,A),(4,0,B),(5,1,B)])]:
        for cycle,ready,payload in events:rows[cycle+delay]['m'][sink]=port(1,ready,payload)
    return rows
def build():
    result=[]
    def add(name,rows,status='PASS',category=None,plan=PLAN):
        result.append(dict(name=name,rows=rows,episodes=deepcopy(plan),expected_status=status,expected_category=category))
    add('independent_consumer_stalls',base())
    add('legal_five_cycle_delay',base(5))
    r=base(3)
    for row in r:
        for p in [row['s']]+row['m']:
            if not p['valid']:p.update(data=0xff,last=1)
    add('invalid_payload_changes',r)
    r=base(2)
    for row in r:
        for p in [row['s']]+row['m']:
            if not p['valid']:p.update(data='xx',last='z')
    add('invalid_payload_unknowns',r)
    r=empty()
    for i,payload in enumerate([A,B]):r[i].update(s=port(1,1,payload),m=[port(1,1,payload),port(1,1,payload)])
    add('zero_cycle_combinational',r)
    r=empty()
    for i,payload in enumerate([A,B]):r[i]['s']=port(1,1,payload);r[i+1]['m'][0]=port(1,1,payload);r[i+2]['m'][1]=port(1,1,payload)
    add('simultaneous_enqueue_and_dequeue',r)
    r=base()
    for i in [4,5]:r[i]['m'][1]=port()
    add('last_transaction_lost',r,'FUNCTION_FAIL','MISSING_TRANSACTION')
    r=base();r[8]['m'][0]=port(1,1,B)
    add('late_extra_duplicate',r,'FUNCTION_FAIL','UNEXPECTED_TRANSACTION')
    r=base()
    for i in [1,2]:r[i]['m'][0]=port(1,r[i]['m'][0]['ready'],B)
    for i in [3,4]:r[i]['m'][0]=port(1,r[i]['m'][0]['ready'],A)
    add('ordered_beats_swapped',r,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL')
    r=base()
    for i in [1,2]:r[i]['m'][0]['data']^=1
    add('accepted_payload_corrupted',r,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL')
    r=base()
    for i in [1,2]:r[i]['m'][0]['last']^=1
    add('accepted_last_corrupted',r,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL')
    r=base();r[2]['m'][0]['data']^=1
    add('stalled_payload_changed',r,'FUNCTION_FAIL','BACKPRESSURE_FAIL')
    r=base();r[2]['m'][0]['last']^=1
    add('stalled_last_changed',r,'FUNCTION_FAIL','BACKPRESSURE_FAIL')
    r=base();r[2]['m'][0]['valid']=0
    add('stalled_valid_withdrawn',r,'FUNCTION_FAIL','BACKPRESSURE_FAIL')
    r=empty()
    for row in r:row['s']=port(1,0,A)
    add('never_accepts_source',r,'FUNCTION_FAIL','LIVENESS_FAIL')
    r=empty();r[0]['s']=port(1,1,A);r[1]['s']=port(1,1,B)
    add('accepted_but_beyond_horizon',r,'FUNCTION_FAIL','MISSING_TRANSACTION')
    r=base();r[0]['s']['ready']=0
    add('source_changes_while_stalled',r,'INPUT_PROTOCOL_FAIL','INPUT_PROTOCOL_FAIL')
    r=base();r[3]['m'][0]['valid']='x'
    add('unknown_valid_control',r,'TRACE_INVALID')
    add('insufficient_fair_drain',base()[:6],'TRACE_INVALID')
    r=base();r[5]['cycle']=6
    add('missing_cycle',r,'TRACE_INVALID')
    reset_plan=[dict(beats=[list(A),[0x33,1]],termination='reset'),dict(beats=[[0x44,1]],termination='drain')]
    r=empty();r[0]['s']=port(1,1,A);r[2]['rst']=1
    r[2]['s']=port('x','x',('xx','x'));r[2]['m']=[port('x','x',('xx','x')),port('x','x',('xx','x'))]
    r[3]['s']=port(1,1,(0x44,1));r[4]['m']=[port(1,1,(0x44,1)),port(1,1,(0x44,1))]
    add('declared_reset_cancels_inflight',r,plan=reset_plan)
    q=deepcopy(r);q[3]['m'][0]=port(1,1,A)
    add('stale_output_after_reset',q,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL',reset_plan)
    assert len(result)==22
    return result
