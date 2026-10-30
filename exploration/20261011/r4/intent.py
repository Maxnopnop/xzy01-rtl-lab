"""Bounded two-serialization temporal contract interpreter; never eval/exec model text."""
import ast,json,re
import tasks
MAX_BYTES=16384
OPS={ast.Add:lambda a,b:a+b,ast.Sub:lambda a,b:a-b,ast.BitAnd:lambda a,b:a&b,ast.BitOr:lambda a,b:a|b,ast.BitXor:lambda a,b:a^b}
CMP={ast.Eq:lambda a,b:a==b,ast.NotEq:lambda a,b:a!=b,ast.Lt:lambda a,b:a<b,ast.LtE:lambda a,b:a<=b,ast.Gt:lambda a,b:a>b,ast.GtE:lambda a,b:a>=b}
class Invalid(Exception):
    def __init__(self,status,message):self.status=status;self.message=message
def expression(text,names):
    if not isinstance(text,str) or len(text)>4096:raise Invalid('UNSUPPORTED','Expression size/type')
    try:tree=ast.parse(text,mode='eval').body
    except SyntaxError:raise Invalid('IR_INVALID','Expression syntax') from None
    if sum(1 for _ in ast.walk(tree))>512:raise Invalid('UNSUPPORTED','Expression nodes')
    def validate(n):
        if isinstance(n,ast.Constant) and type(n.value)==int and 0<=n.value<=65535:return
        if isinstance(n,ast.Name) and n.id in names:return
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:validate(n.left);validate(n.right);return
        if isinstance(n,ast.Compare) and len(n.ops)==1 and type(n.ops[0]) in CMP:validate(n.left);validate(n.comparators[0]);return
        if isinstance(n,ast.BoolOp) and isinstance(n.op,(ast.And,ast.Or)):
            for v in n.values:validate(v)
            return
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.Not):validate(n.operand);return
        if isinstance(n,ast.IfExp):validate(n.test);validate(n.body);validate(n.orelse);return
        raise Invalid('UNSUPPORTED','Unsupported operator, reference or literal')
    validate(tree);return tree
def evaluate(n,env):
    if isinstance(n,ast.Constant):return n.value
    if isinstance(n,ast.Name):return env[n.id]
    if isinstance(n,ast.BinOp):return OPS[type(n.op)](evaluate(n.left,env),evaluate(n.right,env))
    if isinstance(n,ast.Compare):return int(CMP[type(n.ops[0])](evaluate(n.left,env),evaluate(n.comparators[0],env)))
    if isinstance(n,ast.BoolOp):
        v=[bool(evaluate(x,env)) for x in n.values];return int(all(v) if isinstance(n.op,ast.And) else any(v))
    if isinstance(n,ast.UnaryOp):return int(not evaluate(n.operand,env))
    if isinstance(n,ast.IfExp):return evaluate(n.body if evaluate(n.test,env) else n.orelse,env)
    raise AssertionError('Unvalidated expression')
def parse(raw,representation,task):
    if len(raw.encode('utf-8'))>MAX_BYTES:raise Invalid('EXTRACTION_ERROR','Intent exceeds 16KiB')
    if '```' in raw:raise Invalid('EXTRACTION_ERROR','No fences allowed in either intent format')
    if representation=='structured':
        def unique(pairs):
            d={}
            for k,v in pairs:
                if k in d:raise Invalid('IR_INVALID','Duplicate key')
                d[k]=v
            return d
        try:p=json.loads(raw,object_pairs_hook=unique)
        except (ValueError,TypeError):raise Invalid('EXTRACTION_ERROR','Invalid JSON') from None
    else:
        lines=raw.strip().splitlines();p=dict(timing={},registers={},next={},outputs={})
        if not lines:raise Invalid('EXTRACTION_ERROR','Empty intent')
        timing=re.fullmatch(r'Clock edge (rising|falling); reset (async_low|sync_low|none)\.',lines[0])
        if not timing:raise Invalid('IR_INVALID','Timing sentence')
        p['timing']=dict(edge=timing[1],reset=timing[2])
        for line in lines[1:]:
            reg=re.fullmatch(r'Register (\w+) has width (\d+) and reset (\d+)\.',line)
            nxt=re.fullmatch(r'On the clock edge, set (\w+) to (.+)\.',line)
            out=re.fullmatch(r'Continuously output (\w+) as (.+)\.',line)
            if reg:k='registers';n=reg[1];v=dict(width=int(reg[2]),reset=int(reg[3]))
            elif nxt:k='next';n=nxt[1];v=nxt[2]
            elif out:k='outputs';n=out[1];v=out[2]
            else:raise Invalid('IR_INVALID','Unknown linear sentence')
            if n in p[k]:raise Invalid('IR_INVALID','Duplicate declaration')
            p[k][n]=v
    if not isinstance(p,dict) or set(p)!={'timing','registers','next','outputs'}:raise Invalid('IR_INVALID','Top-level keys')
    if any(not isinstance(p[k],dict) for k in p):raise Invalid('IR_INVALID','Dictionary sections required')
    if set(p['timing'])!={'edge','reset'}:raise Invalid('IR_INVALID','Timing keys')
    if p['timing']['edge'] not in ('rising','falling') or p['timing']['reset'] not in ('async_low','sync_low','none'):raise Invalid('UNSUPPORTED','Timing domain')
    registers=p['registers'];inputs={n for n,w in tasks.TASKS[task]['inputs']}|{'rst_n'}
    if not 1<=len(registers)<=16:raise Invalid('UNSUPPORTED','1..16 registers')
    for n,r in registers.items():
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_]*',n) or n in inputs:raise Invalid('IR_INVALID','Register names')
        if not isinstance(r,dict) or set(r)!={'width','reset'}:raise Invalid('IR_INVALID','Register declaration')
        if type(r['width'])!=int or not 1<=r['width']<=8:raise Invalid('UNSUPPORTED','Register width 1..8')
        if type(r['reset'])!=int or not 0<=r['reset']<(1<<r['width']):raise Invalid('IR_INVALID','Reset value range')
    if set(p['next'])!=set(registers):raise Invalid('IR_INVALID','Every register needs one next expression')
    if set(p['outputs'])!={n for n,w in tasks.TASKS[task]['outputs']}:raise Invalid('IR_INVALID','Output coverage')
    p['trees']={k:{n:expression(e,inputs|set(registers)) for n,e in p[k].items()} for k in ('next','outputs')}
    return p
def serialize(p,representation):
    if representation=='structured':return json.dumps(p,separators=(',',':'))
    lines=[f"Clock edge {p['timing']['edge']}; reset {p['timing']['reset']}."]
    lines += [f"Register {n} has width {r['width']} and reset {r['reset']}." for n,r in p['registers'].items()]
    lines += [f'On the clock edge, set {n} to {e}.' for n,e in p['next'].items()]
    lines += [f'Continuously output {n} as {e}.' for n,e in p['outputs'].items()]
    return '\n'.join(lines)
def run(p,task,rows):
    state={n:r['reset'] for n,r in p['registers'].items()};last=0;answers=[]
    for row in rows:
        edge=row['clk']!=last and row['clk']==(p['timing']['edge']=='rising');reset=not row['rst_n']
        if reset and (p['timing']['reset']=='async_low' or edge and p['timing']['reset']=='sync_low'):state={n:r['reset'] for n,r in p['registers'].items()}
        elif edge:
            env=state|tasks.unpack(task,row['input'])|{'rst_n':row['rst_n']}
            state={n:evaluate(t,env)&((1<<p['registers'][n]['width'])-1) for n,t in p['trees']['next'].items()}
        env=state|tasks.unpack(task,row['input'])|{'rst_n':row['rst_n']};value=0
        for n,w in tasks.TASKS[task]['outputs']:value=(value<<w)|(evaluate(p['trees']['outputs'][n],env)&((1<<w)-1))
        answers.append(value);last=row['clk']
    return answers
def check(raw,representation,task,rows):
    try:p=parse(raw,representation,task);answers=run(p,task,rows)
    except Invalid as e:return dict(status=e.status,stage='intent',message=e.message,mismatches=[]),None
    mismatch=[dict(event=i,expected=r['expected'],observed=a,category=r['category']) for i,(r,a) in enumerate(zip(rows,answers)) if r['expected']!=a]
    return dict(status='FUNCTION_FAIL' if mismatch else 'PASS',stage='intent',checks=len(rows),errors=len(mismatch),mismatches=mismatch[:8]),answers
