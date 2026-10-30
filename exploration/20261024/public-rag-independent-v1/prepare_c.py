"""One-shot assembly from sealed A/B/protocol. No network or model calls."""
import json,hashlib,datetime,importlib.util,time
from pathlib import Path
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(p,x):
    assert not p.exists(),p
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
for stage in ['A','B','protocol']:
    lock=read(P/(stage+'-lock.json'))
    assert set(lock)=={f.relative_to(P/stage).as_posix() for f in (P/stage).rglob('*') if f.is_file()}
    assert all(sha(P/stage/n)==h for n,h in lock.items())
assert not (P/'C').exists(),'No reretrieval or overwrite'
cfg=read(P/'protocol/overlay.json');route=read(P/'protocol/route.json');sel=read(P/'B/selection.json')
ids=sel['selected_ids'];assert len(ids)<=8
put(P/'plan.json',{'status':'PREPARED_NOT_RELEASED','created_utc':utc(),'task_order':ids,'models':cfg['models'],'conditions':cfg['conditions'],'samples':2,'planned_slots':len(ids)*12,'executed':0,'model_calls':0,'eda_calls':0,'technical_release':False,'production_ledger':False,'all_tasks_conditional':True,'independent_oracle_passes':0,'gate':'Coordinator and user review; future executor mapping/reference validation separately frozen; old release/ledger cannot be reused'})
put(P/'plan-lock.json',{n:sha(P/n) for n in ['A-lock.json','A-seal.json','B-lock.json','B-seal.json','protocol-lock.json','plan.json','prepare_c.py','review_b.py','review_notes.json','fetch_b.py','prepare_a.py','static_inventory.py']})
put(P/'C/start.json',{'utc':utc(),'a_lock_sha256':sha(P/'A-lock.json'),'b_lock_sha256':sha(P/'B-lock.json'),'plan_lock_sha256':sha(P/'plan-lock.json'),'retrieval_count_before':0})
spec=importlib.util.spec_from_file_location('frozen_retriever',P/'A/retriever.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
chunks=read(P/'A/chunks.json');system=(P/'A/system.txt').read_bytes().decode();template=(P/'A/context-template.txt').read_bytes().decode()
slots=[];stats=[]
doc=['# 独立通用文档 RAG：用户审核包',
     '状态 PREPARED_NOT_RELEASED。20个新候选静态核查，2题条件纳入、18题排除；24个拟调用槽全部NOT_STARTED。0模型/embedding/rerank/编译/仿真/SAT/综合；未创建生产账本或technical-release。未补足8题，未扩候选。',
     '## 方法依据与隔离边界',
     'A在读取新候选前封存：完整lowRISC Verilog Coding Style Guide，commit 9c15ff5dce23eef969e00ab3715153967419eadd，CC-BY-4.0，lowRISC contributors。使用缓存完整原文而非旧精选片段；1来源、48段，逐行贪心<=2048字符、全覆盖无筛主题，可重构原文件。切分可能跨Markdown围栏，不修整。来源/许可SHA见A/source-manifest.json，完整原文/许可证见A/sources。它是风格指南而非语言标准。',
     '检索为新stdlib TF-IDF cosine：(1+ln tf)×(ln((1+N)/(1+df))+1)，L2；token规则[a-z_][a-z0-9_]*、lower；无stopwords/stemming/同义词/扩写，top3正分，平分按ID，无命中为空。算法一般依据 https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting 。所有数值参数在新题读取前冻结。未使用旧错误/成绩/题目/检索结果调整方法。7项通用词fixture通过，只是软件检查。',
     '当前agent已有历史题目和结果的认知暴露，不能声称认知盲法。时间隔离可核验，不能证明彻底消除认知影响；历史文件此次仅用于排除及不变baseline。公开题训练暴露UNKNOWN。baseline中历史措辞independent evaluator不是独立性证明。指南通用例子可能不符合任务允许构造，原题与system约束优先。',
     '## 来源、候选与参考局限',
     'NVlabs/verilog-eval固定commit c498220d0a52248f8e3fdffe279075215bde2da6，MIT，许可证在A/metadata/dataset-LICENSE。156元数据题→83历史/家族排除→73剩余按冻结seed哈希排序→仅首20。60次原始文件GET，60文件93545字节，0重试；没有额外候选。全部原文件、Git blob、SHA和URL见B/access.json。个别prompt/ref/TB作者未建立；commit作者不代替文件作者。参考与TB同源相关，没有独立oracle或正确性签核。',
     '所有20个原TB的wait_for_end_of_timestep只有定义，计分位于测试clk双边沿active区，不能称统一POST/NBA后采样；参考X会屏蔽比较。此次只有静态核查，工具兼容、调度/边界语义及覆盖均未运行验证。不将条件纳入写成PASS。',
     '## 全部新候选决定\n\n|rank|候选|决定|理由|\n|---|---|---|---|']
for r in sel['rows']:
    doc.append(f"|{r['rank']}|{r['id']}|{'条件纳入' if r['selected'] else '排除'}|{r['code']}；{r['contract_zh']} {r['history_review_zh']}|")
doc+=['## 元数据阶段全部83项排除\n\n|ID|原因|\n|---|---|']
for r in cfg['metadata_exclusions']:doc.append(f"|{r['id']}|{r['reason']}|")
doc+=['完整20题接口/复位/有效域/参考/原TB刺激/依赖/作者/采样行号见B/selection.json；完整原题及ref/test（含18排除题）在B/originals，均保持原始字节。',
      '## 统一完整system','```text\n'+system+'\n```','## 冻结context模板','```text\n'+template+'\n```']
for r in sel['rows']:
    if not r['selected']:continue
    task=r['id'];raw=(P/r['bindings']['prompt.txt']['local']).read_bytes();query=raw.decode()
    start=time.perf_counter();rr=m.retrieve(query,chunks);elapsed=time.perf_counter()-start
    chosen=[next(c for c in chunks if c['id']==i) for i in rr['selected_ids']]
    fragments='\n\n'.join(f"[{c['id']}; lowRISC Verilog Coding Style Guide; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in chosen)
    context=template.format(fragments=fragments) if chosen else ''
    rr.update(selected_chunks=chosen,elapsed_seconds=elapsed,context_sha256=digest(context.encode()),a_lock_sha256=sha(P/'A-lock.json'),b_lock_sha256=sha(P/'B-lock.json'))
    put(P/'C/retrieval'/f'{task}.json',rr)
    (P/'C/contexts').mkdir(exist_ok=True);(P/'C/contexts'/f'{task}.txt').write_bytes(context.encode())
    for cond in cfg['conditions']:
        msgs=[{'role':'system','content':system},{'role':'user','content':query+(context if cond=='rag' else '')}]
        put(P/'C/messages'/f'{task}__{cond}.json',msgs)
        for model in cfg['models']:
            for sample in [1,2]:
                sid=f'{task}__{cond}__{model}__s{sample:03d}'
                req={'model':'openai/'+model,'messages':msgs,'stream':False,'provider':{'only':route['provider_only'],'allow_fallbacks':False,'require_parameters':True}}
                dest=P/'C/requests'/f'{sid}.json';put(dest,req)
                slots.append({'ordinal':len(slots)+1,'id':sid,'task':task,'condition':cond,'model':model,'wire_model':req['model'],'sample':sample,'status':'NOT_STARTED','reserved':False,'request':dest.relative_to(P).as_posix(),'request_sha256':sha(dest),'messages_sha256':digest(json.dumps(msgs,ensure_ascii=False,separators=(',',':')).encode()),'expected_provider':route['expected_provider']})
    stats.append({'task':task,'selected_ids':rr['selected_ids'],'scores':[v['score'] for v in rr['rankings'][:3]],'no_hit':rr['no_hit'],'retrieval_seconds':elapsed,'prompt_bytes':len(raw),'context_bytes':len(context.encode())})
    doc+=[f"## {task} — {r['meaning_zh']}",r['contract_zh'],r['history_review_zh'],'原TB与限制：'+r['coverage_zh']]
    for kind,v in r['bindings'].items():doc.append(f"[{kind}]({v['url']}) SHA256 `{v['sha256']}`；Git blob `{v['actual_git_blob']}`")
    doc+=['### 完整原题 = no_rag user','```text\n'+query+'\n```','### 自动检索结果',json.dumps(stats[-1],ensure_ascii=False,indent=2),'全部48段排名、逐词贡献、原始片段及行号见C/retrieval/'+task+'.json。只检索一次，无人工换段或参数回调。','### 完整rag user','```text\n'+query+context+'\n```']
put(P/'C/slots.json',slots);put(P/'C/retrieval-manifest.json',stats)
put(P/'C/summary.json',{'utc':utc(),'retrieval_count':len(stats),'planned_slots':len(slots),'not_started':len(slots),'model_calls':0,'eda_calls':0,'embedding_calls':0,'rerank_calls':0,'usage_tokens':None,'model_cost':None})
doc+=['## 预算与审核边界',f'{len(ids)}×3准确模型×2条件×2样本={len(slots)}最大待审机会；上限96不是必须补足。gpt-5.6-luna/terra/sol各条件完整messages逐字相同，样本重复请求仅槽ID不同；发送字段只model因模型改变，不附参考RTL/TB。temperature/seed/reasoning省略。并发1，180秒/请求，HTTP1MiB、文本128KiB、job8MiB、run512MiB；无8192cap、无整批墙时cap。',
     '预约消耗机会，未知/服务/传输/协议/哈希/资源异常立即停，不自动重试、补样、续写、fallback或扩批；实际usage原始保留，缺失null，费用不编造。固定OpenRouter路线仅离线配置，没有探针、账户访问或新HTTP模型请求。此包未证明服务端无内部包装。旧生产放行/账本及硬编码旧题的执行器均不可直接复用。',
     '先总控及用户审阅本包；工具兼容/参考校准/独立判据和新执行器映射需要另案冻结审核，本次没有运行。仅两题且共享一般组合/索引原语，不能支持总体RAG收益或独立功能族数量结论。下一步尚未授权。',
     '## 阶段封存时间',json.dumps({'A':read(P/'A-seal.json'),'B':read(P/'B-seal.json'),'C_start':read(P/'C/start.json')},ensure_ascii=False,indent=2)]
(P/'USER_REVIEW.md').write_bytes(('\n\n'.join(doc)+'\n').encode())
put(P/'C-lock.json',{f.relative_to(P/'C').as_posix():sha(f) for f in sorted((P/'C').rglob('*')) if f.is_file()})
put(P/'C-seal.json',{'frozen_utc':utc(),'c_lock_sha256':sha(P/'C-lock.json'),'b_lock_sha256':sha(P/'B-lock.json'),'a_lock_sha256':sha(P/'A-lock.json'),'plan_lock_sha256':sha(P/'plan-lock.json'),'retrieval_count':len(stats),'executed_slots':0})
print(json.dumps({'selected':ids,'slots':len(slots),'retrievals':len(stats),'executed':0}))
