"""One-time offline derivation; not a model dispatch command."""
from pathlib import Path
import json
BASE=Path(__file__).resolve().parent;OLD=BASE.parent/'r4'
(BASE/'judge.py').write_bytes((OLD/'judge.py').read_bytes())
src=(OLD/'intent.py').read_text();prefix=src[:src.index('def parse(')]
prefix=prefix.replace('ast.BitXor:lambda a,b:a^b','ast.BitXor:lambda a,b:a^b,ast.LShift:lambda a,b:a<<b,ast.RShift:lambda a,b:a>>b')
prefix=prefix.replace('if isinstance(n,ast.BinOp) and type(n.op) in OPS:validate(n.left);validate(n.right);return','if isinstance(n,ast.BinOp) and type(n.op) in OPS:\n            if isinstance(n.op,(ast.LShift,ast.RShift)) and not (isinstance(n.right,ast.Constant) and type(n.right.value)==int and 0<=n.right.value<=7):raise Invalid("UNSUPPORTED","Shift must be constant0..7")\n            validate(n.left);validate(n.right);return')
parse='''def parse(raw,representation,task):
    if representation!='structured':raise Invalid('UNSUPPORTED','Only S has IR')
    if len(raw.encode())>MAX_BYTES or '```' in raw:raise Invalid('EXTRACTION_ERROR','Intent bytes/fences')
    def unique(pairs):
        d={}
        for k,v in pairs:
            if k in d:raise Invalid('IR_INVALID','Duplicate key')
            d[k]=v
        return d
    try:p=json.loads(raw,object_pairs_hook=unique)
    except (ValueError,TypeError):raise Invalid('EXTRACTION_ERROR','Invalid JSON') from None
    keys={'timing','registers','next_rising','next_falling','outputs'}
    if not isinstance(p,dict) or set(p)!=keys or any(not isinstance(v,dict) for v in p.values()):raise Invalid('IR_INVALID','Dictionary sections')
    if set(p['timing'])!={'reset'}:raise Invalid('IR_INVALID','Timing keys')
    if p['timing']['reset'] not in ('async_low','sync_low','none'):raise Invalid('UNSUPPORTED','Reset domain')
    regs=p['registers'];inputs={n for n,w in tasks.TASKS[task]['inputs']}|{'rst_n'}
    if not 1<=len(regs)<=16:raise Invalid('UNSUPPORTED','Register count')
    for n,r in regs.items():
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*',n) or n in inputs:raise Invalid('IR_INVALID','Register name')
        if not isinstance(r,dict) or set(r)!={'width','reset'}:raise Invalid('IR_INVALID','Register fields')
        if type(r['width'])!=int or not 1<=r['width']<=8:raise Invalid('UNSUPPORTED','Register width')
        if type(r['reset'])!=int or not 0<=r['reset']<(1<<r['width']):raise Invalid('IR_INVALID','Reset range')
    a=set(p['next_rising']);b=set(p['next_falling'])
    if a&b or a|b!=set(regs):raise Invalid('IR_INVALID','Disjoint complete edge banks')
    if set(p['outputs'])!={n for n,w in tasks.TASKS[task]['outputs']}:raise Invalid('IR_INVALID','Output keys')
    p['trees']={k:{n:expression(e,inputs|set(regs)) for n,e in p[k].items()} for k in ('next_rising','next_falling','outputs')}
    return p
def run(p,task,rows):
    state={n:r['reset'] for n,r in p['registers'].items()};last=0;answers=[]
    for row in rows:
        edge=row['clk']!=last;bank='next_rising' if row['clk'] else 'next_falling';reset=not row['rst_n']
        if reset and p['timing']['reset']=='async_low':state={n:r['reset'] for n,r in p['registers'].items()}
        elif edge:
            env=state|tasks.unpack(task,row['input'])|{'rst_n':row['rst_n']}
            for n,t in p['trees'][bank].items():state[n]=p['registers'][n]['reset'] if reset and p['timing']['reset']=='sync_low' else evaluate(t,env)&((1<<p['registers'][n]['width'])-1)
        env=state|tasks.unpack(task,row['input'])|{'rst_n':row['rst_n']};value=0
        for n,w in tasks.TASKS[task]['outputs']:value=(value<<w)|(evaluate(p['trees']['outputs'][n],env)&((1<<w)-1))
        answers.append(value);last=row['clk']
    return answers
'''
(BASE/'intent.py').write_text(prefix+parse+src[src.index('def check('):],encoding='utf-8')

src=(OLD/'runner_v2.py').read_text();head=src[:src.index('def plan(')]
head=head.replace('R4 prepare-gated','R5 prepare-gated').replace("runs/prepared-v2","runs/prepared-v1").replace("assets-v1","assets")
generate=src[src.index('def generate('):src.index('def public_feedback(')]
(BASE/'runner.py').write_text(head+generate+(BASE/'runner_body.py').read_text(),encoding='utf-8')
import sys
sys.path.insert(0,str(BASE))
import tasks
(BASE/'assets').mkdir(exist_ok=True)
for task in tasks.TASKS:
    for label,rows in zip(('public','private'),tasks.datasets(task)):(BASE/'assets'/f'{task}-{label}.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('R5 derived sources/assets; 0 model calls')
