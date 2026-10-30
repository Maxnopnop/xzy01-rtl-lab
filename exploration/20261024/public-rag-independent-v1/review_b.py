"""Human static review transcription; never executes RTL or retrieval."""
import json,hashlib,datetime,re
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
    assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
reviews=read(P/'review_notes.json')
cfg=read(P/'protocol/overlay.json');access=read(P/'B/access.json');inventory=read(P/'B/static-inventory.json');rows=[]
for c in cfg['new_candidates']:
    i=c['id'];ok,title,code,contract,history,coverage=reviews[i]
    inv=next(v for v in inventory if v['id']==i);assert inv['test_helper_name_occurrences']==1 and not inv['includes'] and not inv['readmem']
    bindings={r['kind']:{k:r[k] for k in ['local','url','sha256','expected_git_blob','actual_git_blob']} for r in access if r['task']==i}
    ref=(P/bindings['ref.sv']['local']).read_text();test=(P/bindings['test.sv']['local']).read_text()
    clean=lambda s:re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
    modules=re.findall(r'\bmodule\s+(\w+)',clean(ref+'\n'+test))
    assert sorted(modules)==['RefModule','stimulus_gen','tb']
    assert re.search(r'\bTopModule\s+top_module1\s*\(',test)
    rows.append({'rank':c['rank'],'id':i,'meaning_zh':title,'eligible':ok,'selected':False,'status':'CONDITIONAL_NO_INDEPENDENT_ORACLE' if ok else 'EXCLUDED','code':code,'contract_zh':contract,'history_review_zh':history,'coverage_zh':coverage,'language':'English prompt; SystemVerilog reference/TB, fixed TopModule candidate interface','diagram_or_table':'Any required textual table/diagram reviewed above; never supplemented','signedness':'No signed arithmetic requirement; widths as original interface; four-state unspecified domains not filled','initialization_and_validity':'See per-task contract; no new initialization/reset/output masking added','sampling_zh':'原test计分always位于测试clk双边沿，helper只定义未调用；NBA驱动与active区比较，不保证统一POST/NBA后采样。组合稳定输入阶段比较不等于全时序签核。','dependencies':{'modules':modules,'external_include':[],'readmem':False,'source_files':['prompt.txt','ref.sv','test.sv'],'single_topmodule':'Original TB instantiates TopModule; reference header independently present; static compatible, compile NOT_RUN'},'authorship':{'repository':'NVlabs/verilog-eval','license':'MIT (frozen LICENSE)','snapshot_commit_author':'Nathaniel Pinckney; NOT attributed as individual file author','individual_prompt_ref_test_authors':'UNKNOWN from available files; same repository lineage, no independently authored oracle established'},'reference_independence':'SAME_REPOSITORY_CORRELATED','independent_correctness':'NOT_ESTABLISHED','test_evidence':inv['evidence'],'bindings':bindings})
selected=[r['id'] for r in rows if r['eligible']][:8]
for r in rows:r['selected']=r['id'] in selected
put(P/'B/selection.json',{'utc':utc(),'a_lock_sha256':sha(P/'A-lock.json'),'protocol_lock_sha256':sha(P/'protocol-lock.json'),'candidate_count':len(rows),'selected_ids':selected,'conditional_count':len(selected),'independent_pass_count':0,'rows':rows,'selection_uses_retrieval':False,'new_model_or_eda_calls':0})
put(P/'B-lock.json',{p.relative_to(P/'B').as_posix():sha(p) for p in sorted((P/'B').rglob('*')) if p.is_file()})
put(P/'B-seal.json',{'frozen_utc':utc(),'b_lock_sha256':sha(P/'B-lock.json'),'a_lock_sha256':sha(P/'A-lock.json'),'protocol_lock_sha256':sha(P/'protocol-lock.json'),'selected_ids':selected,'retrieval_calls_so_far':0})
print(json.dumps({'selected':selected,'conditional':len(selected),'excluded':len(rows)-len(selected),'planned_slots':12*len(selected)}))
