"""One-off local preparation; never overwrite frozen files."""
import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parent; ROOT=R.parents[2]; OLD=R.with_name('handshake-dev-v1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (R/'prior-lock.json').exists()
old=json.loads((OLD/'prior-lock.json').read_text())
for name,h in old.items():
 p=Path(name) if Path(name).is_absolute() else ROOT/name
 assert sha(p)==h,name
for p in OLD.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:old[p.relative_to(ROOT).as_posix()]=sha(p)
for name in ['fsm_ir.py','AGENTS.md','test_lab.py','test_batch.py','test_dev.py']:old[name]=sha(ROOT/name)
(R/'prior-lock.json').write_text(json.dumps(old,indent=2)+'\n')
assert not (R/'checker.py').exists()
(R/'checker.py').write_bytes((OLD/'checker.py').read_bytes())
(R/'parse_trace.py').write_text((OLD/'calibrate.py').read_text().split('def parse_trace(p):')[1].split('\ndef main():')[0].join(['def parse_trace(p):','\n']))
(R/'preparation.json').write_text(json.dumps(dict(start_unix=time.time(),prior_count=len(old),checker_sha256=sha(R/'checker.py'),v1_packet_sha256=sha(OLD/'packet-lock.json'),fsm_ir_sha256=sha(ROOT/'fsm_ir.py')),indent=2)+'\n')
print('prior bindings',len(old),'checker copied unchanged')
