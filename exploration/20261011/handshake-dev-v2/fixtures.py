from copy import deepcopy
def port(v=0,r=1,p=(0,0)):return dict(valid=v,ready=r,data=p[0],last=p[1])
def empty():return [dict(cycle=i,rst=0,s=port(),m=[port(),port()]) for i in range(32)]
A=(0x51,1);B=(0xa1,1)
PLAN=[dict(beats=[list(A)],termination='drain')]
RESET=[dict(beats=[list(A),[0x52,1]],termination='reset'),dict(beats=[list(B)],termination='drain')]
def build():
 out=[]
 def add(name,rows,status='PASS',cat=None,plan=PLAN):out.append(dict(name=name,rows=rows,episodes=deepcopy(plan),expected_status=status,expected_category=cat))
 r=empty();r[2].update(s=port(1,1,A),m=[port(1,1,A),port(1,1,A)])
 add('same_edge',r)
 r=empty()
 for i in range(1,5):r[i].update(s=port(1,int(i==4),A),m=[port(1,int(i==4),A),port(1,int(i==4),A)])
 add('early_valid_waits_accept',r)
 r=empty();r[1]['s']=port(1,1,A);r[2]['m'][0]=port(1,1,A)
 for i in range(2,5):r[i]['m'][1]=port(1,0,A)
 for i in range(2,5):r[i]['s']=port(1,0,(0x52,1))
 for i in (5,6):r[i]['rst']=1
 r[7]['s']=port(1,1,B);r[8]['m']=[port(1,1,B),port(1,1,B)]
 add('reset_partial_delivery_cancel',r,plan=RESET)
 bad=deepcopy(r);bad[7]['m'][1]=port(1,1,A)
 add('stale_after_reset',bad,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL',RESET)
 bad=deepcopy(r);bad[7]['m'][1]=port(1,0,A);bad[8]['m'][1]=port(1,1,A)
 add('retained_valid_reset_release',bad,'FUNCTION_FAIL','DATA_OR_ORDER_FAIL',RESET)
 r=empty();r[1]['s']=port(1,1,A);r[3]['m'][0]=port(1,1,A);r[9]['m'][1]=port(1,1,A)
 add('different_consumer_latency',r)
 r=empty()
 for i in range(1,5):r[i]['s']=port(1,int(i==4),A)
 r[1]['m']=[port(1,1,A),port(1,1,A)]
 add('early_consumption_flat_equal',r,'FUNCTION_FAIL','UNEXPECTED_TRANSACTION')
 r=empty();r[1]['s']=port(1,1,A);r[2]['m']=[port(1,0,A),port(1,1,A)];r[3]['m'][0]=port(1,1,(0x50,1))
 add('stall_release_payload_change',r,'FUNCTION_FAIL','BACKPRESSURE_FAIL')
 return out
