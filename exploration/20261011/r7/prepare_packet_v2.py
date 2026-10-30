"""Freeze a negative source-selection decision, never an executable campaign."""
import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,obj):
 p=R/name;data=json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
 if p.exists():
  assert p.read_text(encoding='utf-8')==data,'Resume differs: '+name
  return
 p.write_text(data,encoding='utf-8')
def doc(name,text):
 p=R/name;assert not p.exists(),name
 p.write_text(text.strip()+'\n',encoding='utf-8')
v=read(R/'revisions.json')
rows=[
 ('axis','axis_cobs_decode','rtl/axis_cobs_decode.v','tb/axis_cobs_decode/test_axis_cobs_decode.py','CONTRACT_NOT_EXACT','COBS decoder','No project-exact reuse found. Escaped framing in R5 is related but byte-stuffing/checksum differs from COBS code-length algorithm.','Original test compares decoded frames, not all per-cycle ready/invalid-data values. Partial synchronous reset does not clear payload. Functional COBS oracle is independent algorithmically, but shares author with source test.'),
 ('axis','axis_cobs_encode','rtl/axis_cobs_encode.v','tb/axis_cobs_encode/test_axis_cobs_encode.py','IR_DOMAIN_INCOMPATIBLE','COBS encoder','Same mechanism as candidate1; predeclared at most one COBS source. Related to R5 framing, not labelled exact duplicate.','Two hard-wired DEPTH(256) byte FIFOs; exact upstream implementation state greatly exceeds16x8bits. No arrays in IR. No assertion that every alternative streaming algorithm requires this amount of state. Reducing FIFO depth is source/contract adaptation, not parameter exposed by this module.'),
 ('axis','axis_frame_join','rtl/axis_frame_join.v','tb/test_axis_frame_join_4.py','CONTRACT_NOT_EXACT','Ordered frame concatenation with tag','R4/R6 tagged_join joins matching tags and drops smaller tags; ordered concatenation is different. Shared broad join family is disclosed, not the primary exclusion.','Original test checks tag+four concatenated payloads. README does not fix source-ready pipeline, live tag sampling on every tag byte, or invalid output fields. Source comments and code can define implementation, but are not an independently specified full-cycle contract.'),
 ('axis','axis_frame_length_adjust','rtl/axis_frame_length_adjust.v','tb/axis_frame_length_adjust/test_axis_frame_length_adjust.py','CONTRACT_NOT_EXACT','Runtime padding/truncation','No previous pad/truncate mechanism found in audited task specifications. FIFO/backpressure components overlap broadly.','Original tests assert received length/data prefix/status fields, not exact latency or invalid fields. Full16bit counters/state fit in fixed IR has not been proved; not falsely called an impossible mapping. No width-truncated replacement created.'),
 ('axis','axis_stat_counter','rtl/axis_stat_counter.v','tb/test_axis_stat_counter.py','REFERENCE_RULE_DISAGREEMENT','Triggered byte/frame snapshots','R5 phase_snapshot stores edge samples; stream frame accounting is different. Ordinary counters occur in baseline/Dev10.','Original source counts first non-last word. Directed single-beat last transfer yields byte_count1,frame_count0 and emitted frame-count00. README says counts passing frames; original test examples are multi-beat. Semantics need external resolution before using as truth. Also lacks exact-cycle contract; default six32bit counter/snapshot banks exceed128state bits;8bit parameter observation is separate.'),
 ('axis','axis_broadcast','rtl/axis_broadcast.v','tb/axis_broadcast/test_axis_broadcast.py','CONTRACT_NOT_EXACT','Independent consumer broadcast backpressure','R3 elastic_slot is a single consumer; multiple independent consumption masks are different. Shared skid-buffer mechanics disclosed.','Original tests receive each consumer frame. Native observation shows original data=5a5a while all valid=0; masking only invalid payload would preserve accepted data but fail exact full-output comparison. Mid-reset clears valid/ready, holds old payload. No production judge masking added.'),
 ('axis','axis_tap','rtl/axis_tap.v','tb/test_axis_tap.py','CONTRACT_NOT_EXACT','Nonintrusive tap with truncation under backpressure','No equivalent lossy observer found; generic framed streams overlap with R5.','Original tests check received frames and last-cycle user on truncation. Drop/truncate boundary depends on source implementation buffering and readiness. All invalid output fields/timing not fixed by saved original words. Source initial state and partial reset are implementation facts.'),
 ('axis','axis_async_fifo','rtl/axis_async_fifo.v','tb/axis_async_fifo/test_axis_async_fifo.py','IR_DOMAIN_INCOMPATIBLE','Dual-clock asynchronous FIFO','Base fifo4x8 and R3 elastic_slot share queue mechanisms. CDC adds a new clock domain, not only width/seed variation.','Independent s_clk,m_clk and resets/synchronizers cannot be faithfully replaced by one clk rising/falling and one rst_n. Default4096 depth also exceeds IR state. No tied-clock substitution or digital model treated as analog metastability verification.'),
 ('cells','serial_deglitch','src/cc_serial_deglitch.sv',None,'NEAR_DUPLICATE_FAMILY','Enabled stable-input qualification','paired-v1 debounce3 and R2 already train/test consecutive input qualification. This version adds enable/restart/clear, but retains same deglitch family; conservatively reserved from heldout.','Pinned README explicitly locates cc_serial_deglitch; initial unprefixed path404 retained. Header specifies enabled cycles/restart/current input/clear. Source depends on cc_pkg,register/assert macros. No dependency expansion or executable validation after family exclusion.'),
 ('cells','edge_propagator_ack','src/cc_edge_propagator_ack.sv',None,'IR_DOMAIN_INCOMPATIBLE','CDC pulse with sender acknowledgement','Base edge_detector uses one clock; acknowledged CDC differs. No exact reuse found.','Pinned README maps cc name. Independent clk_tx_i,clk_rx_i and rst_tx_ni,rst_rx_ni plus cc_sync_wedge. Single-clock fixed IR cannot represent arbitrary independent source/receiver schedules/resets without method change.'),
 ('cells','fifo_v3',None,None,'ORIGINAL_ID_UNRESOLVED','Register FIFO','Base fifo4x8/development queues and R3 elastic_slot are related FIFO family.','Original src/fifo_v3.sv404 at pinned revision. README lists cc_fifo; saved cc_fifo is background only, not verified rename equivalence for fifo_v3. No replacement candidate introduced or inferred original identity. Generic FIFO already overlaps baseline family.'),
 ('cells','rr_arb_tree','src/cc_rr_arb_tree.sv',None,'NEAR_DUPLICATE_FAMILY','Round-robin arbitration','R3 rotating_owner trains/tests rotating priority and ownership. Extra tree/fair-throughput/LockIn options are disclosed, but conservatively same arbitration family.','README maps cc name; source documents FairArb/LockIn/AxiVldRdy. Default64 inputs/32bit payload outside small domain but parameter simplification possible; not the primary exclusion. No dependencies or external assertions executed.'),
]
candidates=[]
for i,(repo,name,src,test,decision,mechanism,overlap,reason) in enumerate(rows,1):
 rev=v[repo];base=f"https://github.com/{rev['repo']}/blob/{rev['commit']}/"
 author='Alex Forencich' if repo=='axis' else {'serial_deglitch':'Philippe Sauter','edge_propagator_ack':'Antonio Pullini','rr_arb_tree':'Michael Schaffner','fifo_v3':'UNRESOLVED original author; cc_fifo context: Florian Zaruba'}[name]
 c=dict(candidate=i,original_id=name,repo=rev['repo'],commit=rev['commit'],commit_date=rev['commit_date'],author=author,license='MIT' if repo=='axis' else 'Solderpad Hardware License0.51',mechanism=mechanism,decision=decision,eligible=False,overlap_audit=overlap,reference_boundary=reason,original_spec_url=base+'README.md',original_spec_sha256=sha(R/'upstream'/repo/'README.md'),reference_path=src,reference_url=base+src if src else None,reference_sha256=sha(R/'upstream'/repo/src) if src else None,original_test_path=test,original_test_sha256=sha(R/'upstream'/repo/test) if test else None,project_model_calls=0,method_tuned_on_candidate=False,training_seen='UNKNOWN',minimal_production_adaptation='NONE; no executable task/spec/reference created')
 candidates.append(c)
save('candidates.json',candidates)
inventory=[]
for name in ['tasks/manifest.json','benchmarks/dev10/tasks/manifest.json','benchmarks/dev10/split-lock.json','benchmarks/paired-v1/manifest.json','experiments/fsm48.json','evidence/mutation-v1/contracts-v2.json','exploration/20261011/R1C_PROTOCOL.md','exploration/20261011/r2.py','exploration/20261011/r3/tasks.py','exploration/20261011/r4/tasks.py','exploration/20261011/r5/tasks.py','exploration/20261011/r6/tasks.py']:
 p=ROOT/name;item=dict(path=name,sha256=sha(p))
 if p.suffix=='.json':
  d=read(p)
  if isinstance(d,list):item['task_ids']=[x.get('id') for x in d if isinstance(x,dict)]
  elif isinstance(d,dict):
   if isinstance(d.get('tasks'),list):item['task_ids']=[x.get('id') if isinstance(x,dict) else x for x in d['tasks']]
   elif name.endswith('contracts-v2.json'):item['task_ids']=list(d)
   else:item['split_metadata']=d
 if p.suffix=='.py':
  tree=ast.parse(p.read_text(encoding='utf-8-sig'))
  for node in tree.body:
   if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TASKS' for t in node.targets):
    if isinstance(node.value,ast.Dict):item['task_ids']=[ast.literal_eval(k) for k in node.value.keys]
    elif isinstance(node.value,ast.List):item['task_ids']=ast.literal_eval(node.value)
 inventory.append(item)
save('history-inventory.json',inventory)
method_names=['intent.py','prompts.py','judge.py','PROTOCOL.md','engineering-v2/runner.py','cli_adapter.py','stream_process.py']
method={}
for name in method_names:
 p=ROOT/'exploration/20261011/r6'/name
 if p.exists():method[str(p.relative_to(ROOT))]=sha(p)
 else:raise FileNotFoundError(p)
save('method-lock.json',method)
access=read(R/'source-access.json');files=[]
for p in sorted((R/'upstream').rglob('*')):
 if not p.is_file():continue
 records=[a for a in access if a.get('sha256')==sha(p)]
 assert records,str(p)
 files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),url=records[0]['url'],access_status=records[0]['status']))
assert len(files)<=64 and sum(x['bytes'] for x in files)<=8*1024*1024
save('SOURCE_MANIFEST.json',dict(revisions=v,files=files,file_count=len(files),total_bytes=sum(x['bytes'] for x in files),candidates=candidates,license_files=['upstream/axis/COPYING','upstream/cells/LICENSE'],reuse='Original notices preserved. Internal research audit only; no redistribution/upload undertaken. Calibration TB does not edit upstream source.',not_a_claim='Pinned external authorship is not proof of perfect reference or absence of LLM assistance/training contamination.'))
save('access-adaptation.json',dict(candidate_ids=list(range(1,13)),spec_review=True,hidden_results_accessed=False,natural_model_outputs_accessed=False,model_requests=0,method_changes=[],production_reference_diff=[],calibration_parameter_adaptation={'broadcast_invalid_payload':{'M_COUNT':2,'DATA_WIDTH':8,'KEEP_ENABLE':0,'ID_WIDTH':1,'DEST_WIDTH':1},'stat_counter_singlebeat':{'DATA_WIDTH':8,'KEEP_ENABLE':0,'TAG_WIDTH':8,'TICK_COUNT_WIDTH':8,'BYTE_COUNT_WIDTH':8,'FRAME_COUNT_WIDTH':8}},calibration='Two hand-authored directed source observations. Only scaffolding/parameter setting, original source bytes unchanged. No candidate prompt/IR/generated RTL or performance tuning. No complete alternative functional oracle.'))
decision=dict(kind='R7_SOURCE_SELECTION_PREPARATION_ONLY',status='NO_ELIGIBLE_EXECUTION_CASES',candidate_denominator=12,eligible=0,excluded=12,execution_case_count=0,jobs=[],model_calls=0,reserved_calls=0,execution_plan_sha256=None,preparation_upper_bound_unique_calls=48,reason='No bounded searched candidate simultaneously satisfies prior-family separation, fixed temporal IR, reliable original contract and unchanged exact-output judge. Stop; do not invent fillers or change methods on heldout sources.',future_release='This decision SHA/packet SHA is not a runnable plan authorization.')
save('preparation-decision.json',decision)
doc('PREPARATION.md','''# R7 外部候选准备：负向来源关卡已冻结

12候选完整分母，纳入0，排除12；没有生成执行计划或模型prompt、没有48个预约槽。准备边界48不等于已计划48。**0模型、0预约、0自然候选成绩**，2原参考compile/2sim只作判据/参考观测。交总控审核后停止，不自动换源、扩候选或用同作者原创补数。

固定两个上游commit，所有原字节/许可/作者与URL见SOURCE_MANIFEST.json，完整候选及每项理由见candidates.json。轴流来源已停止维护，按历史版本核查。cells四旧路径404保留，README明确映射三cc名称；fifo_v3身份未核实，不以cc_fifo替代。旧source-download-lock.json是空占位，不作为来源哈希证据；本交付以SOURCE_MANIFEST.json/packet-lock.json为准。

主要缺口：五候选原文字与测试只有流/帧契约，不固定R6逐事件全输出的payload/ready/latency；三候选域不匹配（COBS编码原256FIFO，两个独立CDC时钟）；两候选保守判为旧deglitch/round-robin家族；一个原ID路径身份未核实；计数器存在README计帧与单拍观测的待解歧义。不是已证明作者RTL整体错误，也不是证明没有任何可能适配方法。

广播原源码valid=0时数据5a5a，mid-reset只清valid/ready且保留a7a7。功能等价地屏蔽invalid载荷会在精确全输出比较中不同；没有改R6判据掩码。计数器8bit参数下接收单拍last，输出tag42/tick02/byte01/frame00；保留原输出，未修baseline。原测试只阅读未执行，其独立完整性未通过；不称官方全测试PASS。

冻结四臂方法/IR/分类及预算的承继规则在PROTOCOL.md；执行case为空，execution_plan_sha256=null。packet SHA只标识本负向准备包，不可作模型执行放行。源、计划与成绩R1–R6不动；默认required回归负结果仍保留。本轮无实验运行器改动，不重开运输工程/默认回归或模型服务403请求。

只读核验：从outputs/rtl-batch执行`python exploration/20261011/r7/audit_packet.py`。只读取原源/封存/调用访问记录和本包，不运行参考/模型，不写旧文件。核对prior-lock全部19971原绑定，方法锁、来源哈希、候选12分母、原始compile/sim日志与收尾包哈希。报告中的0纳入是来源关卡负结果，不能得出IR或反馈一般有效/无效。
''')
doc('PROTOCOL.md','''# R7 固定方法承继与停止规则

承继R6（method-lock.json）：S真实显式JSON IR→首次RTL→F/R；D直接RTL D1→无条件D2→F/R，D2固定父样本，不按功能select-best。F两表示仅同公开RTL_spec字段，最多8公开差异；私有IR_spec/RTL_intent只生成完成后评分。所有臂相同原设计事实/公开事件/模型与三阶段机会；这是IR流程对两次RTL流程，不是纯格式/无内部思考对照。没有实现R7专属prompt、事实改写或隐藏向量。

IR不变：单clk/rst_n，rising/falling disjoint寄存器库，最多16个1..8bit寄存器，16KiB JSON；async_low/sync_low/none；表达式常量0..65535、加减/位运算/常量0..7移位/单比较/布尔/条件，4096字符/512AST节点；无数组/第二独立时钟。部分同步reset可用none与显式rst_n条件表达，不据局部reset误判unsupported。宽寄存器可拆分是潜在表达方式，不把所有16bit端口一概说不可支持。判题R6原全输出逐事件精确比较不变。

分类承继：ALL_MATCH；IR_SPEC_DIVERGENCE_RTL_FOLLOWS_IR；RTL_IMPLEMENTATION_DIVERGENCE；RTL_CORRECT_DESPITE_IR_DIVERGENCE；BOTH_DIVERGE_UNATTRIBUTED；REFERENCE_OR_ALIGNMENT_CONFLICT；NOT_ASSESSABLE；其他OBSERVABLE_DIVERGENCE。观察关联不证明内部理解因果，D无IR不归因理解。收益需自然失败见证与参考复核；没有自然错误则定位收益不可估。paired help/harm/no_change只在两臂功能可判时计算，其余inconclusive。格式、unsupported、INPUT_LIMIT、EXTRACTION_ERROR、IR_INVALID、compile/infra、UNKNOWN、PENDING全部保留原计划分母。

若未来另有合格来源及新审核：最多3机制×2重复/6case/48唯一串行逻辑预约，gpt-5.6-sol/low，每策略6结果/18机会、半共享12（具体更小计划必须重新冻结分母，不能硬保6）。180s/次、10800s派发、750MiB派发前阈值、256KiB输入、2MiB软日志、128KiB提取。前4服务gate只查服务，不用成绩挑样。逻辑预约不是底层HTTP数/token硬配额；实际token/cache/reasoning不同、费用无账单UNKNOWN，cache属input/reasoning属output不得重加。服务403/未知停止，无重发/补样/切模型/自动扩批。

本包实际执行case0、预约0、模型0，不存在可放行execution SHA。48仅准备界。保留R6 stream/engineering-v2与只读保守恢复，不改冻结源或据新候选调方法。若将来改握手判据/IR/提示必须在新development工程验证，接触并影响修改的当前候选不得再称未调优heldout。
''')
doc('SOURCE_MANIFEST.md','''# 来源清单与版权保全

机器清单SOURCE_MANIFEST.json保存所有原字节路径/URL/hash/大小及候选对应原README/source/test/作者/许可。来源访问记录source-access.json包含所有成功/404，原请求不重试，0 HTTP403；fixed commit而非可变master作为RTL与test基线。

axis：[原仓库](https://github.com/alexforencich/verilog-axis/tree/48ff7a7e2ef782cf778d47910cf85835c64b1bce)，Alex Forencich，MIT，COPYING与AUTHORS原样保留。README已标deprecated，不把历史源称当前推荐实现。来源文字与测试/RTL主要同作者，不独立于彼此；独立于本项目作者是不同属性。

cells：[原仓库](https://github.com/pulp-platform/common_cells/tree/e73baaec2ca665cd80c3c384e9258e35242b829c)，ETH Zurich/University of Bologna，源码作者Philippe Sauter/Antonio Pullini/Michael Schaffner；Solderpad Hardware License0.51全文保留。cc_fifo作者Florian Zaruba，仅关联背景，fifo_v3原身份未确认。没有联系作者/上传源/凭据或变更仓库许可。

复用范围为本机来源审计与两个手写TB的原源观测；原copyright/license不移除。生产适配diff为空，参数差异完整见access-adaptation.json；不能把改小参数的观测叫原默认配置全测试。没有原外部文字spec与author-ref之外的独立权威golden，未宣称reference已经无界验证、非LLM辅助或训练未见。
''')
doc('REFERENCE_AUDIT.md','''# 外部参考依赖审计

axis链：Alex README/RTL→同作者Python COBS算法或帧关系/struct解包→cocotbext-axi或MyHDL axis_ep握手收发→received-frame assert。作者与本项目独立，但文字/实现/原测试仍可能共同误读；COBS算法不同抽象并非外部第二作者。模块1/3/4/6/7保存原测试不固定所有微架构波形，无法把implementation波形直接当成word-spec完整golden。原test只是阅读，cocotb/MyHDL/axis_ep完整依赖未执行，不能给官方测试PASS。

cells链：README/头注→各外部作者RTL→cc_pkg/registers/assertions宏或cc_sync_wedge/cc_lzc依赖。其作者署名与项目作者不同，依赖正确性、原test独立性与Icarus全配置可执行性未验证。9/12在前置近重复家族关卡排除；10双时钟排除；11原路径身份404未解，不为无用编译下载整个依赖库。

本项目新TB只检查两个手推见证，没有另造完整黄金oracle。广播见证直接观察valid0的payload变化/valid1广播/背压/中途同步reset，不使用原RTL波形自动导出期望。无效payload置零的功能等价变换表明精确逐拍判据可能误报；这是有限见证，不是验证任意新流水线都正确。并未新增生产mask/checker。

stat_counter原文说counts frames，源在last分支只frame_next=0，非last且旧frame0才加1；singlebeat last在8bit计数配置下byte01/frame00。原MyHDL例有多拍17字节数据，不能替代单拍覆盖。原观察原样保存，定性为待解规则/参考冲突，不先宣布作者bug，不修ref或写新的假权威规则；因此不纳入。

source-calibration-v1：2原compile、2sim退出0只说明观测复现。stat帧数0是负向参考观测，不能因进程exit0称参考功能PASS；无模型收益、无自然stage错误。未做全状态/交错事件/无界证明/模拟CDC/PPA。完整receipt包含argv、source/TB哈希、原stdout/stderr及二进制。
''')
coverage='''# 规则—见证—覆盖边界

以下original-test列仅静态阅读；只有标本机观测者实际运行。没有生成R7公开/隐藏模型资产，private/public列均未分派，不把source测试数当覆盖率。

|候选|原规则与原测试见证|本机观测|未覆盖/阻断|
|---|---|---|---|
|1 decode|COBS零分隔/255码/输出帧；原Python算法+recv帧，pause|无|非法码/早last所有交错、复位中断、invalid载荷、exact ready/latency未知|
|2 encode|编码零插入/255段；原encode算法+recv帧|无|256FIFO状态、缓冲满背压、reset边界；固定IR不适配|
|3 join|tag小端+顺序四帧；原四源recv断言|无|live tag逐拍、非0口先valid、busy/ready精确时序、中途复位无完整契约|
|4 adjust|min/max、pad/trunc、original/current length状态；原测试范围/前缀/flags|无|16bit wrap、dynamic config中帧改变、status背压、多拍reset/invalid输出未完整|
|5 counter|trigger dump/reset、byte/frame accounting；原struct帧解包|singlebeat last→byte1/frame0及4输出字节|与一般计帧文字未解；sim源码参数8bit，非默认完整；overflow/trigger同拍/中途reset无全覆盖|
|6 broadcast|每consumer恰一次、独立背压；原recv各帧|valid0载荷变化、一次valid广播、所有消费者stall保持、中途sync reset清valid但payload留存|异步消费者交错消费/满skid/所有reset时点未穷尽；inactive输出不属帧契约|
|7 tap|不影响原流、stall截断置tuser；原last-cycle-user断言|无|截断边界/帧间背压/复位hold，原缓冲位置不属独立文字全周期规则|
|8 asyncFIFO|跨时钟FIFO/overflow/pause/frame；原独立source/sink reset tests|无|CDC模拟物理/任意双时钟；固定单时钟IR无法保留|
|9 deglitch|Threshold enabled周期、restart采当前、clear、async low reset|无|与旧debounce3近族；宏优先级/disable保留历史/reset release需独立证明|
|10 edge ack|发脉冲、保持待ack、双域同步反馈|无|独立reset/时钟/脉冲合并，固定域阻断|
|11 fifo_v3|原ID不存在，cc_fifo只背景|无|原身份/原规格/原test未知；不补为另一题|
|12 arb tree|FairArb下下一个active、LockIn stall、ExtPrio限制|无|旧rotating_owner家族；非2幂树/clear/hold/连续gnt/公平活性未独立验证|

OLD/new-state、reset assert/release、稳定时钟/下降沿保持、优先级、连续事件、背压、边界只在相关规则明确时才可构造权威期望。当前没有公私模型向量/属性资产，不能说已满足这些覆盖。两TB使用无timescale的逻辑#2间隔，仅逻辑离散事件，不声明2ns或模拟物理复位。没有synthetic模型负例、隐藏自然输出或成绩筛选。
'''
doc('COVERAGE.md',coverage)
doc('SPLIT.md','''# 历史排重与候选保留访问

完整12候选未向模型发送；本项目方法在来源查看前固定，0自然输出/0隐藏成绩访问，不按结果换来源。历史排重输入与hash在history-inventory.json，覆盖base20、Dev10及split、FSM48、paired、R1 timed开发5族、R2、R3/R4/R5/R6原task文字，未重评分任何旧RTL。逐候选语义关系在candidates.json，不以端口名/位宽差异宣称新机制。

serial_deglitch与paired debounce3、rr_arb_tree与R3 rotating_owner保守排除同家族；不是断言源码字面相同。FIFO基础语义已训练，fifo_v3原ID另有身份缺口。COBS与R5 escaped/checksum frame不同算法、ordered frame_join与R4/R6 tag-match join不同；广播多consumer与R3单elastic slot不同，但这些差别不能解决精确时序契约关卡。普通计数/时序元素重叠不自动等于近重复，具体理由保留。

标签：12 source-review candidates，0 adopted heldout、0 execution case、0最终集成绩。公开外部来源不保证模型训练未见。独立署名作者不保证原文字/ref/test互相独立；维护者署名不排除未披露LLM辅助。本次原源码/规则与小量TB观察接触全部记录，没有改提示/IR/判据。

若未来因本次AXI差异改方法，这些接触候选必须作为development/measurement-development，不能用于验证同一方法改进的未调优保留收益。另一次来源/方法准备需明确新范围，不能自动扩12分母。重复采样是题内repeat，非新独立任务。
''')
errors=read(R/'preparation-errors.json');errors.append({'operation':'stage classification source lookup r6/runner_body.py','status':'PATH_NOT_FOUND','resolution':'Use frozen R6 PROTOCOL and engineering-v2/runner.py; no retry or source modification'})
(R/'preparation-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':decision['status'],'candidates':12,'eligible':0,'source_files':len(files),'source_bytes':sum(x['bytes'] for x in files),'new_model_calls':0}))
