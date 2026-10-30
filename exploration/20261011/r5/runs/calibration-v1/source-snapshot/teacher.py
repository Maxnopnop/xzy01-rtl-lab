"""Artificial correct contracts and deterministic AST->SV calibration only."""
import ast,json
import tasks,intent
def contract(task):
    regs={'r_'+n:dict(width=w,reset=0) for n,w in tasks.TASKS[task]['outputs']};nxt={n:n for n in regs};fall={}
    if task=='phase_snapshot':
        fall={'r_sampled':'0 if clear_sample else data if capture else r_sampled'};nxt.pop('r_sampled');nxt.update(r_visible='r_sampled if publish else r_visible',r_published='publish')
    elif task=='escape_frame':
        literal='feed and r_active and (r_escaped or symbol==3)'
        end='feed and r_active and not r_escaped and symbol==1'
        start='feed and not r_escaped and symbol==0'
        nxt.update(r_active=f'0 if flush or ({end}) else 1 if ({start}) else r_active',r_escaped='0 if flush else (0 if r_escaped else 1 if r_active and symbol==2 else r_escaped) if feed else r_escaped',r_work_sum=f'0 if flush or ({end}) or ({start}) else r_work_sum ^ symbol if ({literal}) else r_work_sum',r_work_count=f'0 if flush or ({end}) or ({start}) else r_work_count+1 if ({literal}) else r_work_count',r_last_sum=f'r_work_sum if not flush and ({end}) else r_last_sum',r_last_count=f'r_work_count if not flush and ({end}) else r_last_count',r_completed=f'1 if not flush and ({end}) else 0')
    else:
        bit='(1 if release_id==0 else 2 if release_id==1 else 4 if release_id==2 else 8)'
        mask=f'(r_occupied & (15 ^ {bit}) if release else r_occupied)'
        # Select by each pointer's circular priority; no hidden auxiliary assignment order.
        def select(bit_result=False):
            choices=[]
            for h in range(4):
                e='0' if bit_result else '4'
                for j in reversed(range(4)):
                    k=(h+j)%4;e=f'({1<<k if bit_result else k} if ({mask} & {1<<k})==0 else {e})'
                choices.append(e)
            answer=choices[3]
            for h in reversed(range(3)):answer=f'({choices[h]} if r_hint=={h} else {answer})'
            return answer
        choice=select()
        ok=f'allocate and {mask}!=15'
        setbit=select(True)
        nxt.update(r_occupied=f'{mask} | {setbit} if {ok} else {mask}',r_hint=f'({choice}+1)&3 if {ok} else r_hint',r_last_alloc=f'{choice} if {ok} else r_last_alloc',r_alloc_valid=f'1 if {ok} else 0',r_rejected=f'1 if allocate and {mask}==15 else 0')
    return dict(timing=dict(reset='async_low'),registers=regs,next_rising=nxt,next_falling=fall,outputs={n:'r_'+n for n,w in tasks.TASKS[task]['outputs']})
def convert(task,p):
    q=intent.parse(json.dumps(p),'structured',task)
    def expr(n):
        if isinstance(n,ast.Name):return n.id
        if isinstance(n,ast.Constant):return "32'd"+str(n.value)
        if isinstance(n,ast.BinOp):return '('+expr(n.left)+{ast.Add:'+',ast.Sub:'-',ast.BitAnd:'&',ast.BitOr:'|',ast.BitXor:'^',ast.LShift:'<<',ast.RShift:'>>'}[type(n.op)]+expr(n.right)+')'
        if isinstance(n,ast.Compare):return '('+expr(n.left)+{ast.Eq:'==',ast.NotEq:'!=',ast.Lt:'<',ast.LtE:'<=',ast.Gt:'>',ast.GtE:'>='}[type(n.ops[0])]+expr(n.comparators[0])+')'
        if isinstance(n,ast.BoolOp):return '('+(' && ' if isinstance(n.op,ast.And) else ' || ').join(expr(v) for v in n.values)+')'
        if isinstance(n,ast.UnaryOp):return '(!'+expr(n.operand)+')'
        return '('+expr(n.test)+' ? '+expr(n.body)+' : '+expr(n.orelse)+')'
    decl=lambda n,w:('['+str(w-1)+':0] ' if w>1 else '')+n
    t=tasks.TASKS[task];ports=['input clk,rst_n']+['input '+decl(n,w) for n,w in t['inputs']]+['output '+decl(n,w) for n,w in t['outputs']]
    lines=['module '+task+'('+','.join(ports)+');']+['reg '+decl(n,r['width'])+';' for n,r in p['registers'].items()]
    for bank,edge in [('next_rising','posedge'),('next_falling','negedge')]:
        if not p[bank]:continue
        lines+=['always @('+edge+' clk or negedge rst_n) begin if(!rst_n) begin']+[n+' <= '+str(p['registers'][n]['reset'])+';' for n in p[bank]]+['end else begin']+[n+' <= '+expr(e)+';' for n,e in q['trees'][bank].items()]+['end end']
    lines+=['assign '+n+' = '+expr(e)+';' for n,e in q['trees']['outputs'].items()]+['endmodule'];return '\n'.join(lines)
