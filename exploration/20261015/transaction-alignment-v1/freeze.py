"""Stage A only: JSON/AST/hash/file checks. No target import or tool execution."""
import ast,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2];OLD=ROOT/'exploration/20261011';V2=OLD/'handshake-dev-v2';ADD=OLD/'design-addendum-v1';R6=OLD/'r6'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 assert not (R/'plan.json').exists() and not (R/'run-v1').exists(),'Prepare once, no overwrite/run'
 prior=read(V2/'prior-lock.json')
 for name,h in list(prior.items()):
  p=Path(name) if Path(name).is_absolute() else ROOT/name
  assert sha(p)==h,name
 prior={((Path(n) if Path(n).is_absolute() else ROOT/n).relative_to(ROOT).as_posix()):h for n,h in prior.items()}
 for folder,expected in [(V2,'c614a32526e2fa0cb182be7b9dde7aca6e6249df54169a2b190da1f5569eaf16'),(ADD,'090fa59f73bc8355a52d15fc7158e368a6fa94e7c6355a962c4043baf975f012')]:
  assert sha(folder/'packet-lock.json')==expected
  for n,h in read(folder/'packet-lock.json').items():assert sha(folder/n)==h,n
  for p in folder.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:prior[p.relative_to(ROOT).as_posix()]=sha(p)
 for n,h in read(ADD/'source-lock.json').items():assert sha(ROOT/n)==h,n
 prepared=R6/'runs/prepared-v2';r6plan=read(prepared/'plan.json')
 assert sha(prepared/'plan.json')==read(prepared/'plan-lock.json')['sha256']=='f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4'
 for n,h in r6plan['source_hashes'].items():
  p=ROOT/n;assert sha(p)==h,n;prior[p.relative_to(ROOT).as_posix()]=h
 for p in [prepared/'plan.json',prepared/'plan-lock.json',prepared/'preparation-lock.json']:
  prior[p.relative_to(ROOT).as_posix()]=sha(p)
 assert sha(R/'spec_checker.py')==sha(V2/'checker.py')
 save(R/'prior-lock.json',prior)
 python_files=sorted(R.glob('*.py'))
 for p in python_files:ast.parse(p.read_text(),filename=str(p))
 # Mirror only structural/literal bounds; do NOT call R6 parse/expression/run.
 ir=read(R/'broadcast-ir.json');assert set(ir)=={'timing','registers','next_rising','next_falling','outputs'}
 assert ir['timing']=={'reset':'sync_low'} and ir['next_falling']=={}
 assert set(ir['next_rising'])==set(ir['registers']) and 1<=len(ir['registers'])<=16
 for n,v in ir['registers'].items():assert set(v)=={'width','reset'} and 1<=v['width']<=8 and 0<=v['reset']<1<<v['width']
 meta=ast.parse((R/'metadata.py').read_text());ports={}
 for n in meta.body:
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('INPUTS','OUTPUTS'):ports[n.targets[0].id]=ast.literal_eval(n.value)
 assert set(ir['outputs'])=={n for n,w in ports['OUTPUTS']}
 names={n for n,w in ports['INPUTS']}|set(ir['registers'])|{'rst_n'}
 allowed=(ast.Expression,ast.Constant,ast.Name,ast.Load,ast.BinOp,ast.Add,ast.Sub,ast.BitAnd,ast.BitOr,ast.BitXor,ast.LShift,ast.RShift,ast.Compare,ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.BoolOp,ast.And,ast.Or,ast.UnaryOp,ast.Not,ast.IfExp)
 for section in ('next_rising','outputs'):
  for text in ir[section].values():
   tree=ast.parse(text,mode='eval');assert len(text)<=4096 and sum(1 for _ in ast.walk(tree))<=512
   for node in ast.walk(tree):
    assert isinstance(node,allowed),type(node).__name__
    if isinstance(node,ast.Name):assert node.id in names
    if isinstance(node,ast.Constant):assert type(node.value)is int and 0<=node.value<=65535
    if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.LShift,ast.RShift)):assert isinstance(node.right,ast.Constant) and 0<=node.right.value<=7
 assert (R/'broadcast-ir.json').stat().st_size<=16384
 tree=ast.parse((R6/'intent.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');loop=next(n for n in fn.body if isinstance(n,ast.For))
 assert ast.unparse(loop.body[-1])=="last = row['clk']"
 cases=read(R/'cases.json');assert cases['denominator']==len(cases['cases'])==12 and sum(not c.get('skip') for c in cases['cases'])==11
 assert len({c['id'] for c in cases['cases']})==12
 for c in cases['cases']:
  assert set(c['expected'])=={'ir_spec','rtl_spec','intent'}
 tools=read(R/'tools.json')
 for t in tools['tools']:assert sha(Path(t['path']))==t['sha256']
 src=R6/'intent.py'
 save(R/'current-ir-source.json',dict(path=src.relative_to(ROOT).as_posix(),sha256=sha(src),r6_plan_sha256=sha(prepared/'plan.json'),numbered_lines=[dict(line=i+1,text=t) for i,t in enumerate(src.read_text().splitlines())]))
 save(R/'static-validation.json',dict(status='STATIC_STRUCTURE_ONLY_NOT_CALIBRATED',python_ast_files=len(python_files),ir_registers=len(ir['registers']),ir_bytes=(R/'broadcast-ir.json').stat().st_size,cases=12,scheduled_pairs=11,not_evaluable_expected=4,prior_bindings=len(prior),r6_source_bindings=len(r6plan['source_hashes']),target_module_imports=0,ir_parse_calls=0,ir_runs=0,compile_calls=0,sim_calls=0,default_calls=0,model_calls=0,limitations=['No target parser or evaluation invoked','No Verilog compiler/linter run','AST-yield semantic equivalence not tested','No runtime/tool --version calls; binary SHA and PE metadata only']))
 excluded={'plan.json','plan-lock.json','PREPARATION.json'}
 sources={p.relative_to(R).as_posix():sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in excluded}
 plan=dict(status='PREPARED_NOT_EXECUTED',created_date='2026-10-15',kind='SAME_AUTHOR_DEVELOPMENT_PHASE_A',required_release='Coordinator approval bound to exact SHA of this plan; not yet granted',denominator=12,cases=cases['cases'],source_hashes=sources,limits=dict(ir_executions=11,compile=11,sim=11,cycles_per_trace=80,events_per_trace=160,workers=1,ir_seconds=30,compile_seconds=15,sim_seconds=10,wall_seconds=1800,disk_bytes=250*1024*1024,retries=0),new_model_calls=0,production_integration=False,external_tasks_authorized=False,old_calibration='v2 original15/16 full conditions, exit1 preserved',old_default='24tests/3failure/1error/2skip/exit1 preserved, not rerun')
 save(R/'plan.json',plan);digest=sha(R/'plan.json');save(R/'plan-lock.json',dict(sha256=digest))
 for n,h in sources.items():assert sha(R/n)==h,n
 assert set(sources)=={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and p.name not in excluded}
 assert not (R/'run-v1').exists()
 save(R/'PREPARATION.json',dict(status='FROZEN_AWAITING_COORDINATOR_REVIEW_NOT_EXECUTED',plan_sha256=digest,source_bindings=len(sources),prior_bindings=len(prior),denominator=12,scheduled_pairs=11,ir_runs=0,compile=0,sim=0,default=0,model=0,new_external_candidates=0,phase_b_released=False,static_validation_sha256=sha(R/'static-validation.json'),plan_lock_sha256=sha(R/'plan-lock.json')))
 print(json.dumps(read(R/'PREPARATION.json')))
if __name__=='__main__':main()
