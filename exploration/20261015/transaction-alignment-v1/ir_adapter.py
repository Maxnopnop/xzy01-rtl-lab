"""Stage B only. Explicitly instrument current R6 run as a streaming generator.
No language extension: insert one `yield value` after last-clock update.
This adapter's equivalence is an unverified part of the proposed experiment.
"""
import ast,importlib.util,sys
from collections import deque
from pathlib import Path
import metadata
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
class Feed:
 def __init__(self):self.events=deque()
 def __iter__(self):return self
 def __next__(self):
  if not self.events:raise StopIteration
  return self.events.popleft()
def load_stream():
 path=ROOT/'exploration/20261011/r6/intent.py'
 # Only in a fresh child process; no original TASKS/source file mutation.
 assert 'intent' not in sys.modules and 'tasks' not in sys.modules
 sys.modules['tasks']=metadata
 spec=importlib.util.spec_from_file_location('alignment_current_r6_intent',path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 tree=ast.parse(path.read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
 loop=next(n for n in run.body if isinstance(n,ast.For))
 assert ast.unparse(loop.body[-1])=="last = row['clk']"
 loop.body.append(ast.Expr(value=ast.Yield(value=ast.Name(id='value',ctx=ast.Load()))))
 run.name='run_stream';new=ast.fix_missing_locations(ast.Module(body=[run],type_ignores=[]))
 ns=dict(mod.__dict__);exec(compile(new,str(path)+'#yield-adapter','exec'),ns)
 return mod,ns['run_stream']
