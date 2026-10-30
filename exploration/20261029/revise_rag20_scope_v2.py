import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OLD=ROOT/'rag20-five-model-proposal-v1'
NEW=ROOT/'rag20-five-model-proposal-v2'
NEW.mkdir(exist_ok=False)
def read(n):return json.loads((OLD/n).read_bytes())
def save(n,v):(NEW/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
removed={'openai/gpt-5.6-sol','openai/gpt-5.6-terra'}
budget=read('budget.json');budget['models']=[m for m in budget['models'] if m['id'] not in removed]
oa=[m for m in budget['models'] if m['id'].startswith('openai/')]
ds=[m for m in budget['models'] if m['id'].startswith('deepseek/')]
for label,models in [('openai',oa),('deepseek_increment',ds),('all',budget['models'])]:
 budget[label+'_scenario_usd']=round(sum(m['scenario_usd'] for m in models),8)
 budget[label+('_cap_usd' if label=='deepseek_increment' else '_conditional_cap_usd')]=round(sum(m['conditional_cap_usd'] for m in models),8)
budget['with_20_percent_reserve']=round(budget['all_conditional_cap_usd']*1.2,8)
budget['proposed_api_spend_envelope_usd']=20
budget['pricing_snapshot']='2026-10-29 v1 saved public metadata; no new network requests'
save('budget.json',budget)
slots=[]
for row in read('proposal-slots.json'):
 if row['model'] in removed:continue
 row=dict(row,parent_proposal_id=row['id'],id='proposal300v2-%03d'%(len(slots)+1))
 slots.append(row)
assert len(slots)==300 and all(not r['reserved'] and not r['executable'] for r in slots)
save('proposal-slots.json',slots)
policy=read('proposal-policy.json');policy.update(status='LOCAL_DESIGN_REVIEW_ONLY_NOT_RELEASED',current_arithmetic='20*5*3*1=300',removed_models=sorted(removed),coordinator_delivery=False,review_owner='current conversation')
policy.pop('expanded_arithmetic',None)
policy['blockers']=[x.replace('420-call','300-call').replace('coordinator design review','design review in current conversation') for x in policy['blockers']]
save('proposal-policy.json',policy)
save('task-labels-copy.json',read('task-labels-copy.json'))
save('parent-bindings.json',{n:hashlib.sha256((OLD/n).read_bytes()).hexdigest() for n in ['REVIEW.txt','budget.json','proposal-slots.json','proposal-policy.json','review-lock.json']})
note='''范围修订 v2（2026-10-29）
按用户指示暂不加入GPT-5.6 Sol及Terra。
当前模型：GPT-4o、GPT-4.1、GPT-5.6 Luna、DeepSeek V4.1 Flash-1017、DeepSeek V4 Pro-0813。
20题×5模型×3条件×每格1次=300次；不是180次。300个设计槽未预约、不可执行。
三条件及RAG候选保持v1的设计建议：无RAG、48段TF-IDF、同资料库ChipMind混合检索适配。
旧20题标签、判据问题和v1所有限制保留，不重选题，不改旧实验成绩。
v1的420次方案和送审记录保留，仅作为历史版本；后续由当前对话审核，不再发送总控。
本版预算替代v1的45美元提案：情景3.2668美元；有条件token上限费用15.0798336美元；
20%余量后18.09580032美元，建议20美元API包络。税费/充值费用等不含。
这些不是已执行消费限制，输入/输出各8192 token的计数与限额仍待离线实现验证。
模型、embedding、EDA调用均0。本版未重新联网，复用当日价格证据。
'''
(NEW/'REVISION.txt').write_text(note,encoding='utf-8')
save('audit.json',dict(models=len(budget['models']),slots=len(slots),generation_calls=0,embedding_calls=0,eda_calls=0,network_requests=0,coordinator_messages=0,parent_files_unchanged=all(hashlib.sha256((OLD/n).read_bytes()).hexdigest()==h for n,h in json.loads((NEW/'parent-bindings.json').read_bytes()).items())))
print(json.dumps({'models':[m['id'] for m in budget['models']],'slots':len(slots),'scenario':budget['all_scenario_usd'],'conditional_cap':budget['all_conditional_cap_usd'],'reserve':budget['with_20_percent_reserve']},ensure_ascii=False))
