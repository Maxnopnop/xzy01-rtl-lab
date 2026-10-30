"""Freeze completed run/report only; no experiment execution or target imports."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.with_name('transaction-alignment-v1');ROOT=R.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (R/'packet-lock.json').exists()
plan=read(P/'plan.json');assert sha(P/'plan.json')==read(P/'plan-lock.json')['sha256']=='c2aeef0482f72c1deded6bf45d6aae6012a889dc4f71801a633e4aa04e942c10'
for n,h in plan['source_hashes'].items():assert sha(P/n)==h,n
run=P/'run-v1';evidence=read(run/'evidence-lock.json')
for n,h in evidence.items():assert sha(run/n)==h,n
assert set(evidence)=={p.relative_to(run).as_posix() for p in run.rglob('*') if p.is_file() and p.name!='evidence-lock.json'}
audit=read(R/'audit.json');assert audit['run_bindings']==len(evidence)==270 and audit['new_ir_or_tool_runs']==0
bindings={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(P.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
save(R/'execution-bindings.json',bindings)
excluded={'packet-lock.json','seal-verification.json'}
packet={p.relative_to(R).as_posix():sha(p) for p in sorted(R.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded};save(R/'packet-lock.json',packet)
for n,h in bindings.items():assert sha(ROOT/n)==h,n
for n,h in packet.items():assert sha(R/n)==h,n
assert set(packet)=={p.relative_to(R).as_posix() for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
receipt=dict(status='SEALED_EXECUTED_AWAITING_COORDINATOR_INDEPENDENT_AUDIT',plan_sha256=sha(P/'plan.json'),run_evidence_sha256=sha(run/'evidence-lock.json'),run_bindings=len(evidence),execution_binding_count=len(bindings),report_packet_sha256=sha(R/'packet-lock.json'),report_packet_count=len(packet),audit_sha256=sha(R/'audit.json'),actual_calls=dict(ir=11,compile=11,sim=11),executed_pairs=11,predeclared_not_run=1,outer_exit=0,run_bytes=sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),model_calls=0,new_external_candidates=0,old_negative_results='Preserved unchanged',repeat_experiments_during_report=0)
save(R/'seal-verification.json',receipt);print(json.dumps(receipt))
