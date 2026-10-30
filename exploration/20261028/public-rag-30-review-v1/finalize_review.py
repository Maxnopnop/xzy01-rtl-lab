"""Append-only review packaging. No retrieval, calibration, network or dispatch."""
import collections,contextlib,copy,hashlib,io,json,re,socket,subprocess,sys
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def txt(p,s):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
def deny(*a,**k):raise RuntimeError('Review-only: network/process/dispatch forbidden')
original=read(P/'console-package.json');original_sha=sha(P/'console-package.json')
main=copy.deepcopy(original)
main['name']+='-main36'
main['slots']=[dict(s,ordinal=i+1) for i,s in enumerate(s for s in original['slots'] if s['analysis_category']=='MAIN_CANDIDATE')]
main['max_calls']=36
main['auxiliary_candidates']=[]
main['archived_auxiliary_candidates']=original['auxiliary_candidates']
main['parent_draft']={'path':'console-package.json','sha256':original_sha,'max_calls':300,'role':'ARCHIVED_CANDIDATE_PLAN_NOT_APPROVED'}
main['review_boundary']='Only 3 MAIN_CANDIDATE tasks; 36 slots. Candidate ceiling 360 is historical scope, not permission.'
assert len(main['slots'])==36
put(P/'console-package-main36.json',main)
note='Prob107_fsm1s：原题明确同步高有效复位，但未显式指定 posedge；参考采用 posedge。不能将参考的边沿选择写成原题已明确要求。维持 AUXILIARY，不修改原题、参考、检索、messages 或既有300槽清单。'
put(P/'review-addendum.json',{'Prob107_fsm1s':note,'recommended_review_manifest':'console-package-main36.json','recommended_opportunities':36,'archive_only_manifest':'console-package.json','archive_opportunities':300,'auxiliary_opportunities_not_authorized':264,'release_created':False})
checks=[]
def check(name,ok,detail=None):
 checks.append({'name':name,'pass':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name)
before=read(P/'preservation-before.json');lock=read(P/'v3-source-lock.json')
check('155 prior evidence and console bindings unchanged',all(sha(R/n)==h for n,h in before.items()),len(before))
check('13 current v3 sources unchanged',all(sha(R/n)==h for n,h in lock.items()),len(lock))
alock=read(P/'prior/A-lock.json')
check('14 exact frozen A copies',all(sha(P/'A'/n)==h for n,h in alock.items()),len(alock))
review=read(P/'reference-risk-review.json')['rows'];receipt={x['task']:x for x in read(P/'calibration/receipt-audit.json')['rows']}
chunks=read(P/'A/chunks.json');template=(P/'A/context-template.txt').read_bytes().decode();system=(P/'A/system.txt').read_bytes().decode()
for row in review:
 task=row['id']
 for s in row['source_bindings']:
  raw=(P/s['local']).read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  check(task+'/'+s['kind']+' SHA256+Git blob',sha(P/s['local'])==s['sha256'] and blob==s['expected_git_blob'])
 c=read(P/'calibration'/task/'compile.json');v=read(P/'calibration'/task/'simulate.json');a=receipt[task]
 matches=[re.fullmatch(r'Mismatches: (\d+) in (\d+) samples',line) for line in v['stdout'].splitlines()];matches=[m for m in matches if m]
 check(task+' raw calibration receipt',c['returncode']==v['returncode']==0 and not any(x.get(k) for x in (c,v) for k in ('timeout','output_limit')) and len(matches)==1 and tuple(map(int,matches[0].groups()))==(0,a['expected_checks']))
 check(task+' original parser failure preserved',read(P/'calibration'/task/'result.json')['status']=='SIMULATION_OR_RECEIPT_FAILURE' and sha(P/'calibration'/task/'result.json')==a['original_result_sha256'])
 prompt=(P/next(s['local'] for s in row['source_bindings'] if s['kind']=='prompt.txt')).read_bytes().decode()
 rr=read(P/'retrieval'/f'{task}.json');chosen=[next(c for c in chunks if c['id']==n) for n in rr['selected_ids']]
 fragments='\n\n'.join(f"[{c['id']}; lowRISC Verilog Coding Style Guide; lines {c['start_line']}-{c['end_line']}]\n{c['text']}" for c in chosen)
 context=template.format(fragments=fragments) if chosen else ''
 check(task+' saved ranking and context',rr['query']==prompt and len(rr['rankings'])==48 and rr['rankings']==sorted(rr['rankings'],key=lambda x:(-x['score'],x['chunk_id'])) and rr['selected_ids']==[x['chunk_id'] for x in rr['rankings'] if x['score']>0][:3] and rr['selected_chunks']==chosen and (P/'contexts'/f'{task}.txt').read_bytes()==context.encode())
 for arm in ('rag','no_rag'):
  check(task+'/'+arm+' exact original prompt and frozen wrapper',read(P/'messages'/f'{task}__{arm}.json')==[{'role':'system','content':system},{'role':'user','content':prompt+(context if arm=='rag' else '')}])
for name,count in [('console-package.json',300),('console-package-main36.json',36)]:
 obj=read(P/name)
 check(name+' all bound files',all(sha(P/n)==h for n,h in obj['files'].items()))
 check(name+' slots budget',len(obj['slots'])==obj['max_calls']==count and all(s['status']=='NOT_STARTED' and s['reserved'] is False for s in obj['slots']))
 check(name+' no hidden token cap',all(not {'max_tokens','max_completion_tokens','max_output_tokens'}&read(P/s['request']).keys() for s in obj['slots']))
 groups=collections.Counter((s['task'],s['model'],s['condition']) for s in obj['slots'])
 check(name+' balanced two samples',set(groups.values())=={2})
check('main subset unchanged except ordinal',all({k:v for k,v in s.items() if k!='ordinal'}=={k:v for k,v in next(o for o in original['slots'] if o['id']==s['id']).items() if k!='ordinal'} for s in main['slots']))
check('300 archive bytes unchanged',sha(P/'console-package.json')==original_sha)
sys.path.insert(0,str(R));import console_bridge_v3 as b;import console_cli_v3 as cli
preview=[]
with patch.object(socket.socket,'connect',deny),patch.object(socket,'create_connection',deny),patch.object(subprocess,'Popen',deny),patch.object(b,'transport',deny),patch.object(b.Package,'dispatch',deny):
 for name,count in [('console-package.json',300),('console-package-main36.json',36)]:
  buffer=io.StringIO()
  with contextlib.redirect_stdout(buffer):rc=cli.main(['preview','--manifest',str(P/name),'--release',str(P/'NO_RELEASE_EXISTS.json')])
  out=json.loads(buffer.getvalue());put(P/(name.replace('.json','-preview.json')),out)
  check(name+' actual CLI preview',rc==0 and len(out['rows'])==count and all(s['status']=='NOT_STARTED' for s in out['rows']) and out['network_requests']==0)
  pkg=b.Package(P/name)
  check(name+' no model state created',not pkg.state.exists())
  preview.append({'manifest':name,'sha256':sha(P/name),'count':count,'state_exists':pkg.state.exists(),'network_requests':0})
check('no placeholder release exists',not (P/'NO_RELEASE_EXISTS.json').exists())
check('old evidence unchanged after preview',all(sha(R/n)==h for n,h in before.items()))
put(P/'offline-package-audit.json',{'checks':checks,'pass':True,'preview':preview,'new_retrieval':0,'new_compile':0,'new_simulate':0,'model_calls':0,'school_calls':0,'release_created':False,'technical_boundary':'DRAFT_REVIEW label alone is not an execution gate. No release exists; dispatch requires separately reviewed exact manifest and all permitted slot IDs.'})
orig=['# 30题原始提示词全文\n\n以下逐题正文来自冻结上游文件；中文说明另见 USER_REVIEW.md，未写入请求。权威字节以链接原文件及SHA为准。\n']
cards=[]
table=['|序号|题目|分类|原回执检查数|检索片段|','|---|---|---|---:|---|']
for row in review:
 task=row['id'];bindings={s['kind']:s for s in row['source_bindings']};s=bindings['prompt.txt'];rr=read(P/'retrieval'/f'{task}.json')
 orig.append(f"\n## {row['rank']}. {task}\n\n[原文件]({s['local']}) · [固定commit来源]({s['url']})\n\nSHA256 `{s['sha256']}`\n\n````text\n"+(P/s['local']).read_bytes().decode()+"\n````\n")
 table.append(f"|{row['rank']}|{task}|{row['category']}|{receipt[task]['expected_checks']}|{', '.join(rr['selected_ids'])}|")
 card=f"\n## {row['rank']}. {task} — {row['category']}\n\n{row['meaning_zh']}。\n\n契约：{row['static_contract_review_zh']}\n\n历史/近重复：{row['overlap_review_zh']}\n\n原测试覆盖：{row['coverage_zh']}\n\n"
 if task=='Prob107_fsm1s':card+=f'补充审核说明（优先于旧摘要的简写）：{note}\n\n'
 card+=' · '.join(f"[{kind}]({v['local']}) / [固定来源]({v['url']})" for kind,v in bindings.items())+'\n\n'
 card+='\n'.join(f"- {kind} SHA256 `{v['sha256']}`；Git blob `{v['expected_git_blob']}`" for kind,v in bindings.items())+'\n\n'
 card+=f"[完整排名及命中词](retrieval/{task}.json) · [实际上下文](contexts/{task}.txt) · [原始仿真回执](calibration/{task}/simulate.json)\n"
 cards.append(card)
txt(P/'ORIGINAL_PROMPTS.md',''.join(orig))
report='''# 30候选有限准备审核材料

建议先审独立的 **36槽主候选包**：Prob055_conditional、Prob124_rule110、Prob072_thermostat × 3模型 × 有/无RAG × 2样本。此为待审方案，尚未执行或放行。

- [主候选36槽清单](console-package-main36.json)：max_calls=36，保持原请求字节和槽ID，仅连续重编号。
- [300槽归档草案](console-package.json)：25题×12，其中36主候选机会、264辅助机会；不得将口头36许可用于此300槽包。辅助题没有自动执行授权。
- 总分母30题：3主候选、22辅助、5不得执行；360为筛选时最大机会数，不需凑满。
- [30题完整原文](ORIGINAL_PROMPTS.md)、[逐题审阅与行号证据](reference-risk-review.json)、[补充说明](review-addendum.json)、[离线核验](offline-package-audit.json)。

## 取材、方法与时间线

现有已采用20题，加冻结剩余顺序21—30，共30题。scope.json在新增正文读取前冻结；未按检索命中或预期成绩选题。90源文件中60复用旧缓存，30次公开GET取得新增10题文件，0重试。Git blob与SHA256逐一核对；来源NVlabs/verilog-eval固定commit c498220d0a52248f8e3fdffe279075215bde2da6，MIT许可。官方仓库来源不等于逐题作者已核实，也不证明模型训练未见。

RAG完全复用已冻结的48段TF-IDF A包（14文件相同），lowRISC固定commit 9c15ff5dce23eef969e00ab3715153967419eadd，CC-BY-4.0。A旧封存2026-10-24 07:00:39 UTC早于旧B首次读题07:00:59 UTC。每题仅调用原检索器一次，保留全部48排名、命中词贡献、top3、上下文；30题均非空命中。这不代表资料有帮助。未调库、词表、参数、排名、片段或包装，也未调用embedding。

原题全文原字节保留，中文解释独立。同题同条件三模型及两样本的system/user内容完全相同；有RAG仅追加冻结上下文。参考和TB未拼入消息。旧20采用记录与历史/近重复标签完整保留，本轮分类不倒改旧采用决定或成绩。

## 参考校准与保留的失败

本轮恰好30次Icarus编译、30次vvp仿真，未重跑：仅在独立dut.sv中将参考模块名改为TopModule，原参考和TB不改。原始日志全部退出0、无超时，零失配且检查数为正。这仅证明同源参考别名在原TB下自洽，不能证明参考独立正确、覆盖完整或真实生成RTL通过。

首版回执解析器未处理Windows CRLF，30个result.json均误报SIMULATION_OR_RECEIPT_FAILURE。这些误报、日志及源码全部保留；receipt-audit.json只读解析现有日志纠正计数，0重跑。编译警告仍保留。旧默认代理回归的3 failure/1 error保留，不重测。原题时钟双边沿active区比较、NBA采样与参考X屏蔽等限制仍存在；学校检查数可能不同，不能以本机计数回填旧成绩。本轮学校工具执行0。

## 模型、预算及解释边界

|OpenRouter ID|角色假设|冻结参数|
|---|---|---|
|openai/gpt-4o-mini|较小/较旧候选|不发送reasoning/temperature/seed|
|openai/gpt-4.1-mini|第二能力档候选|不发送reasoning/temperature/seed|
|openai/gpt-5.6-luna|5.6对照|reasoning.effort=medium|

三个ID来自10月24日已保存的OpenRouter公开目录/端点GET；本轮复用快照，新增目录GET与账户探针均0。固定provider only=[openai]、allow_fallbacks=false、require_parameters=true。公开目录支持参数不证明当前账户/路由可用，未知保持UNKNOWN。较小、较旧不等于已证实RTL较弱；不同架构、训练和推理预算也是混杂因素，不能把差异单独归因为模型新旧。

预算calls_only：36槽推荐待审，300槽仅归档；无8192或其他token cap字段，不设美元硬上限。manifest的max_tokens=null只是记账，实际请求不含此字段。模型/embedding调用0，尚无usage账单，cost=null不能解释为未来免费。若后续获准执行，应保留实际输入/输出/推理/cache token、费用与缺失值；未知调用不重发，错误与负结果不补样。

比较每模型Δ=同题RAG通过率−无RAG通过率，再比较Δ的模型间差异；同时报告帮助、损害、不变和未完成。按题配对，不能把同题重复样本当独立题。主候选仅3题，结论只能是探索性；22辅助应另列，近重复题族不能冒充独立新题。没有收益也保留，不据结果调RAG或补题。

## 控制台审核边界

绑定console v3 recovery-r1现行13文件锁，bridge SHA为492bb008b8d42c524a9241ea437ecb9b89f004cc9a1a08028687f69ec12816f5。两个清单均通过真实console_cli_v3 preview，全部NOT_STARTED；预览时网络、子进程、transport和dispatch被禁止。没有调用学校或生成后处理，没有建立模型运行状态。

DRAFT_REVIEW字段本身不是技术执行门。执行还必须有绑定清单SHA、源码、模型及全部槽ID的独立release；本包无release。36包和300包是重叠方案，不能同时放行，否则会重复调用同一批主候选。用户仍需审阅原题、三个模型组合及无费用硬上限的预算；本材料不构成执行授权。

旧155项证据/控制台绑定及本轮14个A文件在封包核验时未变。总控另存input-audit.json独立核90源与30组日志；本包未修改总控审计文件。有限准备到此结束，不新增实验。

## 30题分母

'''
txt(P/'USER_REVIEW.md',report+'\n'.join(table)+'\n'+''.join(cards))
txt(P/'COMPLETION.md','有限准备完成。实际CLI两包预览成功；全部未启动；0模型/embedding/学校调用，无release。原误报及默认代理负结果保留。推荐先审36槽，300仅归档。详见USER_REVIEW.md和offline-package-audit.json。\n')
print(json.dumps({'checks':len(checks),'pass':True,'preview':preview},ensure_ascii=False))
