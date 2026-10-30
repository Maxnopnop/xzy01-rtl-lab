"""Same author, separate rule derivation; shares interfaces/packing, not step()."""
import tasks
def run(task,rows):
    last=0;answers=[];tickets={};serial=0;ret=0;rt=0
    busy=done=q=r=remaining=answer_q=answer_r=0
    a=b=None;valid=tag=data=0
    for row in rows:
        x=tasks.unpack(task,row['input']);rise=row['clk']==1 and last==0
        if not row['rst_n']:
            tickets={};serial=0;ret=rt=0;busy=done=q=r=remaining=answer_q=answer_r=0;a=b=None;valid=tag=data=0
        elif rise:
            if task=='ordered_retire':
                if x['flush']:tickets={};ret=rt=0
                else:
                    old=dict(tickets);head=min(old) if old else None;ret=int(head is not None and old[head][1])
                    if ret:rt=old[head][0];del tickets[head]
                    for age,(t,ready) in old.items():
                        if age!=head or not ret:tickets[age]=(t,bool(ready or (x['finish'] and t==x['finish_tag'])))
                    if x['issue'] and len(old)<2 and not any(t==x['issue_tag'] for t,ready in old.values()):tickets[serial]=(x['issue_tag'],False);serial+=1
            elif task=='restoring_divide':
                if x['abort']:busy=done=q=r=remaining=answer_q=answer_r=0
                else:
                    done=0
                    if busy:
                        if x['advance']:
                            remaining-=1
                            if remaining==0:busy=0;done=1;q=answer_q;r=answer_r
                    elif x['start']:
                        if x['denominator']==0:q=15;r=x['numerator'];done=1
                        else:answer_q,answer_r=divmod(x['numerator'],x['denominator']);busy=1;remaining=4
            else:
                if x['clear']:a=b=None;valid=tag=data=0
                else:
                    olda,oldb=a,b
                    if a is None and x['a_valid']:a=(x['a_tag'],x['a_data'])
                    if b is None and x['b_valid']:b=(x['b_tag'],x['b_data'])
                    move=False
                    if olda is not None and oldb is not None:
                        compare=(olda[0]>oldb[0])-(olda[0]<oldb[0])
                        if compare<0:a=None
                        elif compare>0:b=None
                        elif not valid or x['take']:move=True;a=b=None;valid=1;tag=olda[0];data=4*olda[1]+oldb[1]
                    if not move and x['take']:valid=0
        d=dict(count=len(tickets),retired=ret,retired_tag=rt) if task=='ordered_retire' else dict(busy=busy,done=done,quotient=q,remainder=r) if task=='restoring_divide' else dict(a_full=int(a is not None),b_full=int(b is not None),out_valid=valid,out_tag=tag,out_data=data)
        out=0
        for n,w in tasks.TASKS[task]['outputs']:out=(out<<w)|d[n]
        answers.append(out);last=row['clk']
    return answers
