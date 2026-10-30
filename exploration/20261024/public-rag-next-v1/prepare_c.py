"""Frozen assembly, one retrieval per selected task. No HTTP/model/EDA."""
import json,hashlib,datetime,importlib.util,time
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes().decode('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(p,x):
    assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
for stage,folder in [('A','A'),('B','B'),('protocol','protocol')]:
    lock=read(P/(stage+'-lock.json'))
    assert all(sha(P/folder/n)==h for n,h in lock.items())
    assert set(lock)=={f.relative_to(P/folder).as_posix() for f in (P/folder).rglob('*') if f.is_file()}
assert not (P/'C').exists(),'No reretrieval/reassembly over existing C'
selection=read(P/'B/selection.json');cfg=read(P/'protocol/overlay.json');route=read(P/'protocol/route.json')
put(P/'plan.json',{'status':'NOT_STARTED_NOT_RELEASED','created_utc':utc(),'task_order':selection['selected_ids'],'task_count':len(selection['selected_ids']),'models':cfg['models'],'wire_models':cfg['wire_models'],'conditions':cfg['conditions'],'samples':2,'planned_generation_slots':len(selection['selected_ids'])*12,'executed':0,'production_ledger_created':False,'technical_release_created':False,'supersedes_proposals_not_additive':True,'budget_overlay_sha256':sha(P/'protocol/overlay.json'),'route_sha256':sha(P/'protocol/route.json'),'all_tasks_conditional':True,'independent_oracle_passes':0,'execution_gate':'Coordinator review plus explicit user review; new task mapping/calibration must be separately frozen before production; historical direct-api-v1 hardcodes old batch and cannot directly execute these new slots'})
put(P/'plan-lock.json',{n:sha(P/n) for n in ['A-lock.json','A-seal.json','protocol-lock.json','B-lock.json','B-seal.json','plan.json','prepare_c.py','review_b.py','fetch_b.py','prepare_a.py']})
put(P/'C/start.json',{'utc':utc(),'a_lock_sha256':sha(P/'A-lock.json'),'b_lock_sha256':sha(P/'B-lock.json'),'plan_lock_sha256':sha(P/'plan-lock.json'),'retrievals_before':0})
spec=importlib.util.spec_from_file_location('frozen_retriever',P/'A/retriever.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
chunks=read(P/'A/corpus/chunks.json');system=(P/'A/system.txt').read_bytes().decode('utf-8');template=(P/'A/context-template.txt').read_bytes().decode('utf-8-sig');slots=[];stats=[]
doc=['# 下一轮公开原题 RAG 对照：用户待审材料','状态：PREPARED_NOT_RELEASED。20候选静态核查后8题条件纳入、12题排除，拟96槽，全部NOT_STARTED。0模型、0编译/仿真/SAT/综合。无技术放行、无新生产账本。',
'A方法逐字复用：18段lowRISC库，原BM25/stopwords/top3/system/context。原A预算/选题文件仅历史保全，新范围及取消8192硬cap由protocol/overlay.json单独定义。旧240槽及服务错误不重跑，与旧240或三臂216提案不叠加。',
'元数据156题→63项历史/家族排除→剩余93题按原seed排序→只读首20题→8条件纳入。未补候选；不得根据检索或成绩换题。原文完整保存在B/originals，原始字节以文件为准，下文代码块只作展示。',
'所有题及参考来自NVlabs/verilog-eval固定commit c498220d0a52248f8e3fdffe279075215bde2da6，MIT原许可证见A/metadata/dataset-LICENSE。个别文件作者未建立；snapshot作者不是每个ref/test的作者。参考/test同库相关、非独立oracle；公开不等于训练未见，训练暴露UNKNOWN。',
'八题均为组合逻辑接口，含组合FSM转移，无寄存器时序题。不能用于声称中途复位、边沿间保持或握手事务收益。相关题组：019与087共享a&~b，114与106共享表查找形式；逐题报告，不冒称八个完全独立功能族。',
'原TB均在测试clk双边沿直接评分，wait_for_end_of_timestep仅定义；不宣称POST/NBA后统一采样。参考X会屏蔽比较：094边界两位为原题明示dont-care，和被排除084初始存储未定义不同。143题面允许multi-hot但原TB只测one-hot，覆盖缺口保留。',
'## 冻结时序',json.dumps({'A':read(P/'A-seal.json'),'B':read(P/'B-seal.json'),'C_start':read(P/'C/start.json')},ensure_ascii=False,indent=2),
'## 全部候选分母\n\n|序号|题目|决定|依据|\n|---|---|---|---|']
for r in selection['rows']:doc.append(f"|{r['rank']}|{r['id']}|{'条件纳入' if r['selected'] else '排除'}|{r['code']}：{r['history_review_zh'] if 'HISTORY' in r['code'] or 'DUPLICATE' in r['code'] else r['contract_zh']}|")
doc+=['\n完整逐题契约/语言/初始化/接口/依赖/测试行号/作者来源/排除理由见 B/selection.json；全部原候选（包括排除题）保留60原文件及SHA/Git blob。','## 完整统一system（逐字复用，不向模型加入中文评语）','```text\n'+system+'\n```','## 原始context-template','```text\n'+template+'\n```']
for row in selection['rows']:
    if not row['selected']:continue
    task=row['id'];raw=(P/row['bindings']['prompt.txt']['local']).read_bytes();query=raw.decode('utf-8')
    t=time.perf_counter();rr=m.retrieve(query,chunks);elapsed=time.perf_counter()-t
    selected=[next(c for c in chunks if c['id']==i) for i in rr['selected_ids']]
    fragments='\n\n'.join(f"[{c['id']}; {c['section']}; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in selected)
    context=template.format(fragments=fragments) if selected else ''
    rr.update(selected_chunks=selected,elapsed_seconds=elapsed,context_sha256=digest(context.encode()),a_lock_sha256=sha(P/'A-lock.json'),b_lock_sha256=sha(P/'B-lock.json'))
    put(P/'C/retrieval'/f'{task}.json',rr)
    (P/'C/contexts').mkdir(exist_ok=True);(P/'C/contexts'/f'{task}.txt').write_bytes(context.encode())
    for cond in cfg['conditions']:
        user=query+(context if cond=='rag' else '')
        messages=[{'role':'system','content':system},{'role':'user','content':user}]
        put(P/'C/messages'/f'{task}__{cond}.json',messages)
        for model in cfg['models']:
            for sample in [1,2]:
                sid=f'{task}__{cond}__{model}__s{sample:03d}'
                req={'model':'openai/'+model,'messages':messages,'stream':False,'provider':{'only':route['provider_only'],'allow_fallbacks':False,'require_parameters':True}}
                dest=P/'C/requests'/f'{sid}.json';put(dest,req)
                slots.append({'ordinal':len(slots)+1,'id':sid,'task':task,'condition':cond,'model':model,'wire_model':req['model'],'sample':sample,'status':'NOT_STARTED','reserved':False,'request':dest.relative_to(P).as_posix(),'request_sha256':sha(dest),'messages_sha256':digest(json.dumps(messages,ensure_ascii=False,separators=(',',':')).encode()),'expected_provider':route['expected_provider']})
    stats.append({'task':task,'selected_ids':rr['selected_ids'],'scores':[x['score'] for x in rr['rankings'][:3]],'no_hit':rr['no_hit'],'retrieval_seconds':elapsed,'prompt_bytes':len(raw),'context_bytes':len(context.encode())})
    doc += [f"## {task} — {row['meaning_zh']}",f"条件纳入；独立正确性NOT_ESTABLISHED。{row['history_review_zh']}",'契约：'+row['contract_zh'],'测试与局限：'+row['coverage_zh'],row['sampling_zh']]
    for k,v in row['bindings'].items():doc.append(f"[{k}]({v['url']}) SHA256 `{v['sha256']}`；Git blob `{v['actual_git_blob']}`")
    doc += ['### 完整原题 / no_rag user','```text\n'+query+'\n```','### 实际自动检索',json.dumps(stats[-1],ensure_ascii=False,indent=2),'完整18段排名及逐词分数见 C/retrieval/'+task+'.json；未人工替换。','### 完整 rag user（原题+原模板+原片段）','```text\n'+query+context+'\n```',f'两条件共享上述统一system；完整发送JSON为C/requests/{task}__{{condition}}__{{model}}__s00{{sample}}.json；不包含ref/test或本文件中文解释。']
put(P/'C/slots.json',slots);put(P/'C/retrieval-manifest.json',stats)
put(P/'C/summary.json',{'utc':utc(),'retrieval_count':len(stats),'planned_slots':len(slots),'not_started':len(slots),'model_calls':0,'eda_calls':0,'embedding_calls':0,'rerank_calls':0,'account_requests':0,'usage_tokens':None,'model_cost':None,'usage_note':'No model request; no observed usage, not a measured zero-token model response'})
doc += ['## 预算、停止与待审边界',f'{len(stats)}题×3指定模型×有/无RAG×2样本={len(slots)}调用机会，全部NOT_STARTED。每次只生成RTL，无IR/反馈/补样。固定题序、条件序、模型序、样本序；并发1、单请求180秒，无8192输出硬cap，无整批墙时上限；保留HTTP1MiB/文本128KiB及后续执行器磁盘保护。实际input/output/reasoning/cache与费用如实记录，缺失null，不把无cap解释成无限资源。',
'预约消耗机会；首次HTTP服务错/transport/UNKNOWN/模型provider不匹配/哈希或资源异常即停，不自动retry/fallback/续写/补样/扩批。不得新建接入探针；本轮只复用已审OpenRouter路线配置，不访问账户或模型。',
'当前仅构造拟发送完整请求，未实际发送，也未证明服务端无内部包装/重试。旧direct-api-v1硬绑定旧20题，不可将本包直接交旧入口执行；将来新批映射、工具兼容校准、独立判据、生产账本/技术放行必须另行审核，不能复用旧账本或旧放行。',
'额外独立验证见independent-validation-proposal.json：仅具体候选计划和待审真值表达，没有运行。审阅者已见参考，故本草案不冒充独立oracle；需独立人员按原题复核。原题、测试与参考始终不改。','冻结后停止。由总控独立核查并呈用户审核；本材料不授权模型运行、方法调优或下一轮筛选。']
(P/'USER_REVIEW.md').write_text('\n\n'.join(doc)+'\n',encoding='utf-8')
put(P/'C-lock.json',{p.relative_to(P/'C').as_posix():sha(p) for p in sorted((P/'C').rglob('*')) if p.is_file()})
put(P/'C-seal.json',{'frozen_utc':utc(),'c_lock_sha256':sha(P/'C-lock.json'),'b_lock_sha256':sha(P/'B-lock.json'),'a_lock_sha256':sha(P/'A-lock.json'),'plan_lock_sha256':sha(P/'plan-lock.json'),'retrieval_count':len(stats),'executed_slots':0})
print(json.dumps({'conditional_tasks':len(stats),'planned_slots':len(slots),'retrievals':len(stats),'executed':0}))
