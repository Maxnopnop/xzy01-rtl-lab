"""Artificial correct IR calibration only; never supplied to model campaign."""
import json
def make(task):
    if task=='ordered_retire':
        regs={'c':2,'t0':2,'t1':2,'d0':1,'d1':1,'ret':1,'rt':2}
        pop='(c > 0 and d0 == 1)';push='(issue == 1 and c < 2 and (c == 0 or issue_tag != t0) and (c < 2 or issue_tag != t1))'
        zero='flush == 1';after=f'(c - 1 if {pop} else c)'
        expr={'c':f'0 if {zero} else {after} + {push}',
              't0':f'0 if {zero} else issue_tag if ({push} and {after} == 0) else t1 if {pop} else t0',
              't1':f'0 if {zero} else issue_tag if ({push} and {after} == 1) else 0 if {pop} else t1',
              'd0':f'0 if ({zero} or ({push} and {after} == 0)) else (d1 or (finish == 1 and finish_tag == t1 and c > 1)) if {pop} else (d0 or (finish == 1 and finish_tag == t0 and c > 0))',
              'd1':f'0 if ({zero} or {pop} or ({push} and {after} == 1)) else (d1 or (finish == 1 and finish_tag == t1 and c > 1))',
              'ret':f'0 if {zero} else {pop}','rt':f'0 if {zero} else t0 if {pop} else rt'}
        out=dict(count='c',retired='ret',retired_tag='rt')
    elif task=='restoring_divide':
        regs={'b':1,'done_r':1,'qo':4,'ro':4,'n':4,'d':4,'p':5,'q':4,'left':3}
        run='b == 1 and advance == 1';accept='b == 0 and start == 1';z=f'({accept} and denominator == 0)';load=f'({accept} and denominator != 0)';last=f'({run} and left == 1)'
        trial='((p << 1) + (n >> 3))';bit=f'({trial} >= d)';nr=f'({trial} - d if {bit} else {trial})';nq=f'(((q << 1) + {bit}) & 15)'
        expr={'b':f'0 if (abort == 1 or {z} or {last}) else 1 if {load} else b',
              'done_r':f'0 if abort == 1 else 1 if ({z} or {last}) else 0',
              'qo':f'0 if abort == 1 else 15 if {z} else {nq} if {last} else qo',
              'ro':f'0 if abort == 1 else numerator if {z} else {nr} if {last} else ro',
              'n':f'0 if abort == 1 else numerator if {load} else (n << 1) if {run} else n',
              'd':f'0 if abort == 1 else denominator if {load} else d',
              'p':f'0 if (abort == 1 or {load}) else {nr} if {run} else p',
              'q':f'0 if (abort == 1 or {load}) else {nq} if {run} else q',
              'left':f'0 if abort == 1 else 4 if {load} else left - 1 if {run} else left'}
        out=dict(busy='b',done='done_r',quotient='qo',remainder='ro')
    else:
        regs={'af':1,'bf':1,'ov':1,'ot':2,'od':4,'at':2,'ad':2,'bt':2,'bd':2}
        move='(af == 1 and bf == 1 and at == bt and (ov == 0 or take == 1))'
        expr={'af':f'0 if (clear == 1 or {move} or (af == 1 and bf == 1 and at < bt)) else 1 if (af == 0 and a_valid == 1) else af',
              'bf':f'0 if (clear == 1 or {move} or (af == 1 and bf == 1 and bt < at)) else 1 if (bf == 0 and b_valid == 1) else bf',
              'ov':f'0 if clear == 1 else 1 if {move} else 0 if take == 1 else ov',
              'ot':f'0 if clear == 1 else at if {move} else ot','od':f'0 if clear == 1 else (ad << 2) + bd if {move} else od',
              'at':'0 if clear == 1 else a_tag if (af == 0 and a_valid == 1) else at','ad':'0 if clear == 1 else a_data if (af == 0 and a_valid == 1) else ad',
              'bt':'0 if clear == 1 else b_tag if (bf == 0 and b_valid == 1) else bt','bd':'0 if clear == 1 else b_data if (bf == 0 and b_valid == 1) else bd'}
        out=dict(a_full='af',b_full='bf',out_valid='ov',out_tag='ot',out_data='od')
    return json.dumps(dict(timing=dict(reset='async_low'),registers={n:dict(width=w,reset=0) for n,w in regs.items()},next_rising=expr,next_falling={},outputs=out))
