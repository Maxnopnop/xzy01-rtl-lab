"""One offline execution of frozen A retrieval after B selection seal; no network/EDA."""
from pathlib import Path
import json,hashlib,datetime,importlib.util,time,zipfile,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_bytes().decode('utf-8-sig'))
def write(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p)
 p.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
for stage in ['A','B']:
 lock=read(P/f'{stage}-lock.json')
 assert set(lock)=={x.relative_to(P/stage).as_posix() for x in (P/stage).rglob('*') if x.is_file()}
 assert all(sha((P/stage/k).read_bytes())==h for k,h in lock.items())
 assert sha((P/f'{stage}-lock.json').read_bytes())==read(P/f'{stage}-seal.json')[stage.lower()+'_lock_sha256']
assert not (P/'C').exists()
C=P/'C';C.mkdir()
write(C/'start.json',dict(utc=utc(),a_lock_sha256=sha((P/'A-lock.json').read_bytes()),b_lock_sha256=sha((P/'B-lock.json').read_bytes()),selection_sha256=sha((P/'B/selection.json').read_bytes()),model_calls=0,eda_calls=0))
t=time.perf_counter();sp=importlib.util.spec_from_file_location('frozen_retriever',P/'A/retriever.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);import_seconds=time.perf_counter()-t
chunks=read(P/'A/corpus/chunks.json');system=(P/'A/system.txt').read_bytes().decode();template=(P/'A/context-template.txt').read_bytes().decode('utf-8-sig');budget=read(P/'A/budget-policy.json');selection=read(P/'B/selection.json');cov=read(P/'B/coverage.json');source=read(P/'A/corpus/manifest.json')['source']
report=['# 待审公开原题与实际检索\n','状态：PREPARED_BLOCKED。仅离线准备，模型/embedding/rerank/compile/sim/SAT 均0。先总控审核，再由用户确认；本文件不是执行许可。\n',
'资料库与方法在新候选正文读取前冻结。A冻结时间 '+read(P/'A-seal.json')['frozen_utc']+'；B读取开始 '+read(P/'B/start.json')['utc']+'；B选择封存 '+read(P/'B-seal.json')['frozen_utc']+'。A锁 '+sha((P/'A-lock.json').read_bytes())+'。\n',
'156个元数据ID→43个历史/家族排除→113个固定哈希排序→只读取首20个→12个静态合格、8个排除→按固定顺序取首5个；余7个合格但受上限未选，另93个未读。全部理由见 B/selection.json。未使用检索效果选题。\n',
'任务来源 NVlabs/verilog-eval，commit c498220d0a52248f8e3fdffe279075215bde2da6；MIT许可原文见 A/metadata/dataset-LICENSE。模型训练是否见过这些公开题 UNKNOWN；这里只主张未参与本地本方法调整，不主张训练污染已排除。\n',
'所有原题/参考/测试已逐字绑定git blob，原题文件和下方英文段保持字节；中文解释、资格判断、检索片段和system均是分开的项目材料。原参考与测试同源，不是独立oracle。原题仅发送prompt，绝不发送参考/test/中文解释。\n',
'## 项目统一system（不是上游题目）\n\n```text\n'+system+'```\n']
slots=[];stats=[]
for row in selection['rows']:
 if row['id'] not in selection['selected_ids']:continue
 task=row['id'];raw=(P/row['bindings']['prompt.txt']['path']).read_bytes();query=raw.decode();t=time.perf_counter();result=mod.retrieve(query,chunks);secs=time.perf_counter()-t
 selected=[next(c for c in chunks if c['id']==i) for i in result['selected_ids']]
 fragments='\n\n'.join(f"[{c['id']}; {c['section']}; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in selected)
 context=template.format(fragments=fragments) if selected else ''
 result.update(selected_chunks=selected,elapsed_seconds=secs,a_lock_sha256=sha((P/'A-lock.json').read_bytes()),b_lock_sha256=sha((P/'B-lock.json').read_bytes()),context_sha256=sha(context.encode()))
 write(C/'retrieval'/f'{task}.json',result)
 (C/'contexts').mkdir(exist_ok=True);(C/'contexts'/f'{task}.txt').write_bytes(context.encode())
 for condition in budget['conditions']:
  user=query+(context if condition=='rag' else '')
  messages=[dict(role='system',content=system),dict(role='user',content=user)]
  write(C/'messages'/f'{task}__{condition}.json',messages)
  (C/'users').mkdir(exist_ok=True);(C/'users'/f'{task}__{condition}.txt').write_bytes(user.encode())
  assert user.encode().startswith(raw)
  for model in budget['models']:
   for sample in [1,2]:
    slot=f'{task}__{condition}__{model}__s{sample:03d}'
    request=dict(model=model,messages=messages,stream=False,max_completion_tokens=budget['max_completion_tokens'])
    write(C/'requests'/f'{slot}.json',request)
    slots.append(dict(id=slot,task=task,condition=condition,model=model,sample=sample,status='NOT_STARTED',request=f'C/requests/{slot}.json',request_sha256=sha((C/'requests'/f'{slot}.json').read_bytes()),messages_sha256=sha(json.dumps(messages,ensure_ascii=False,separators=(',',':')).encode()),user_sha256=sha(user.encode()),system_sha256=sha(system.encode())))
 stats.append(dict(task=task,selected_ids=result['selected_ids'],scores=[r['score'] for r in result['rankings'][:3]],no_hit=result['no_hit'],retrieval_seconds=secs,original_bytes=len(raw),context_bytes=len(context.encode()),rag_user_bytes=len(raw)+len(context.encode())))
 report.extend([f"\n## {task}（固定候选序号{row['rank']}）\n",'中文释义：'+row['meaning_zh']+'。\n','入选依据与限制：'+row['reason_zh']+'\n',f"[公开原题]({row['bindings']['prompt.txt']['url']}) · [原参考]({row['bindings']['ref.sv']['url']}) · [原测试]({row['bindings']['test.sv']['url']})\n",'原题 SHA256：'+sha(raw)+'\n','### 完整上游原文\n\n```text\n'+query+'```\n','### 覆盖与独立性\n\n'+cov['per_task'][task]+' 同源参考未运行；新额外验证未适配。\n','### 实际检索（自动取固定top3，无人工替换）\n'])
 for c in selected:
  score=next(r['score'] for r in result['rankings'] if r['chunk_id']==c['id'])
  report.append(f"\n{c['id']} / {c['section']} / score={score!r} / [原文L{c['start_line']}-L{c['end_line']}]({source['document_url']}#L{c['start_line']}-L{c['end_line']}) / SHA256 {c['sha256']}\n\n```text\n{c['text']}\n```\n")
 report.append(f'\n完整18片段排名与逐词贡献：C/retrieval/{task}.json。完整待发messages：C/messages/{task}__no_rag.json 与 {task}__rag.json；三模型两样本引用相同内容，实际服务包装仍待核。\n')
write(C/'slots.json',slots)
write(C/'summary.json',dict(utc=utc(),import_seconds=import_seconds,retrieval_count=len(stats),retrieval_seconds=sum(s['retrieval_seconds'] for s in stats),tasks=stats,planned_slots=len(slots),executed_slots=0,failed_slots=0,unknown_slots=0,not_started_slots=len(slots),model_calls=0,embedding_calls=0,rerank_calls=0,eda_calls=0))
report.extend(['\n## 方法冻结与局限\n','A采用原18片段lowRISC库和原检索器，没有根据新题改资料/分段/停用词/同义词/词形/top-k/排序/包装/预算。纯词法BM25，无词形或同义词处理；完整排名保留。片段是一般风格建议，不是答案，也不是规范语言标准；检索相似度不证明适用性或收益。不得用观察结果重新择题或换片段。\n','\n## 预算与执行门槛\n','五题×三模型×两条件×两样本=60槽，全部NOT_STARTED，替代旧准备、不叠加旧24/60/30槽。每次8192 completion token，最大491520；并发1，单请求180秒，模型阶段12000秒，全批28800秒。返回文本128KiB/HTTP1MiB；不重试、不补样，未知预约占机会且停新调用，403/不支持模型/传输或包装异常立即停。真实token与费用当前0模型调用，未来单价/实际费用UNKNOWN，不能把token上限当固定费用。\n','服务隐藏包装是否一致、completion硬上限是否实际执行、三指定模型与共同参数支持、正式执行器、原参考校准和新题额外验证适配均仍阻断。温度/seed/reasoning统一省略不代表默认行为已证相同。只有本地拟请求一致，未证明实际请求一致。\n','后续参考校准只是另待批准的最多5compile+5sim建议（15s/10s，首次基础设施异常停），本轮不执行；不能重复此前COMSPEC定位或默认代理失败回归。SAT14/32与事件/复位能力需逐题契约审查，不能把未支持题当PASS。\n'])
(P/'USER_REVIEW.md').write_bytes('\n'.join(report).encode())
with zipfile.ZipFile(P/'selected-original-prompts.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for row in selection['rows']:
  if row['id'] in selection['selected_ids']:
   z.writestr(row['id']+'_prompt.txt',(P/row['bindings']['prompt.txt']['path']).read_bytes())
 z.writestr('LICENSE',(P/'A/metadata/dataset-LICENSE').read_bytes())
write(P/'C-lock.json',{x.relative_to(C).as_posix():sha(x.read_bytes()) for x in sorted(C.rglob('*')) if x.is_file()})
write(P/'C-seal.json',dict(frozen_utc=utc(),c_lock_sha256=sha((P/'C-lock.json').read_bytes()),a_lock_sha256=sha((P/'A-lock.json').read_bytes()),b_lock_sha256=sha((P/'B-lock.json').read_bytes()),model_calls=0,eda_calls=0))
print(json.dumps(stats))
