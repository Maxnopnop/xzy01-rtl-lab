"""Record explicit user adoption of all existing20; no fetch/retrieval/model."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
old=P.parent/'public-rag-independent-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((old/'B/selection.json').read_bytes())
lock=json.loads((old/'packet-lock.json').read_bytes())
assert all(sha(old/n)==h for n,h in lock.items())
rows=[]
for r in source['rows']:
    rows.append({'rank':r['rank'],'id':r['id'],'adopted':True,'adoption_basis':'USER_EXPLICIT_ALL20','prior_selected':r['selected'],'prior_code':r['code'],'prior_contract':r['contract_zh'],'prior_overlap_notes':r['history_review_zh'],'source_bindings':r['bindings'],'correctness':'NOT_INDEPENDENTLY_VALIDATED','risk_resolved_by_adoption':False})
assert len(rows)==20 and len({r['id'] for r in rows})==20
out={'status':'ALL20_ADOPTED_RAG_DESIGN_REVIEW_PENDING_NOT_RELEASED','user_instruction':'把这些20道题全部新采用；重新考虑RAG并解释以往使用；不依据之前题目影响设计','meaning':'采用本轮已读的20个候选，不是旧批20题，也不宣称它们均为历史未见或互相独立。用户采用覆盖旧筛选决定，但不消除记录的重叠/规格风险。','source_packet_lock_sha256':sha(old/'packet-lock.json'),'source_packet_files_verified':len(lock),'task_order':[r['id'] for r in rows],'task_count':20,'rows':rows,'proposed_call_opportunities':240,'budget_basis':'20 x 3 exact models x 2 conditions x 2 samples; replaces prior24 proposal, not additive','models':['gpt-5.6-luna','gpt-5.6-terra','gpt-5.6-sol'],'conditions':['no_rag','rag'],'samples':2,'new_payloads_created':False,'rag_method_status':'PROPOSAL_ONLY_NOT_FROZEN','model_calls':0,'new_fetches':0,'new_retrievals':0,'eda_calls':0,'technical_release':False,'no_retry_or_refill':True,'old_packet_unchanged':True,'limitations':['Old exclusion decisions retained as flags, not silently erased','Task prompt/ref/test remain original bytes; RAG cannot fill missing specification values','No causal independence or training-unseen claim','Current agent has task exposure; proposed method must use generic documentation and externally specified procedure, no task-conditioned tuning']}
target=P/'adoption.json';assert not target.exists();target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'adopted':len(rows),'old_risk_records_retained':18,'proposal_opportunities':240,'source_packet_files_verified':len(lock),'new_retrievals':0,'model_calls':0}))
