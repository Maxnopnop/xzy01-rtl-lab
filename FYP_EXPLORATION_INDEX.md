# FYP本机探索入口（2026-10-11）

独立工作目录：[exploration/20261011](exploration/20261011/task_plan.md)。
计划、发现与执行记录分别在该目录的task_plan.md、findings.md、progress.md。
本轮保留冻结历史实验和学校综合记录。预算更新后实际启动4次模型调用，均API_ERROR，0新RTL；16槽未启动。离线新增135次Icarus、5次有界SAT。

- [首轮结论、成功/失败案例与下一轮三路线](exploration/20261011/RESULTS.md)
- [14项候选方向排序与文献/代码核查边界](exploration/20261011/CANDIDATES.md)
- [环境与授权记录](exploration/20261011/ENVIRONMENT.md)
- [独立证据锁、最短反例与SAT轨迹核验](exploration/20261011/verification.json)
- [178份历史RTL逐文件/哈希审计](exploration/20261011/historical-audit.json)
- [复合故障与四格模型协议](exploration/20261011/PROTOCOL.md)、[延迟触发协议](exploration/20261011/DELAYED_PROTOCOL.md)、[SAT协议](exploration/20261011/FORMAL_PROTOCOL.md)

重要发现：v2公开检查检出3119个两处编辑故障；但5个12拍延迟触发故障同时通过v2和旧固定隐藏测试，独立Icarus见证及有界SAT均检出。人工夹具不能当作自然模型错误率或生成收益，旧分数不重写。

## R1b 有限补强（已结束）

[R1b报告与主张—证据—局限—下一实验映射](exploration/20261011/R1B_RESULTS.md)。新增SAT正例/短界限/反例/真实语法错误9格校准；24份历史模型RTL（17原PASS、7原FAIL）在14/32步验证：7原失败的14条反例全部独立Icarus复现，17原PASS未发现新反例，不声称无界正确或方法增益。[独立核验](exploration/20261011/r1b-verification.json)确认首轮1612文件及源码锁不变。

首版换行hash元数据问题另建v2修正，两个run冻结保留、选择/状态一致；本轮实际114个Yosys检查命令、38次Icarus评估（含必要重跑），0新模型调用。一次只读路由检查未确认替代可用端点，没有重试403。

解释收窄：3119是限定IR编辑候选数，首轮仅50个故障候选执行RTL仿真；E4五例是同一种人工前缀克隆机制，有限测试漏检本身不作为新颖性或LLM过拟合证据。

## R1c与R2准备（2026-10-11）

[R1c报告](exploration/20261011/R1C_RESULTS.md)：先10格校准，再64种历史原PASS RTL事件复测，全部PASS，新错误0；独立状态图核验454860事件。补充中途复位/正常保持隔离见证通过，首版初始X隔离失败保留。合计80次Icarus，0模型调用，旧锁/成绩不变、未重试403。

[R2准备](exploration/20261011/R2_PREPARATION.md)：五家族两重复两臂20槽已冻结，15次Icarus离线夹具与26次mock控制流验收通过；20真实调用未启动，等待总控后续放行。没有模型收益估计。

## R2正式放行后完成

[R2真实结果](exploration/20261011/R2_RESULTS.md)：20槽全启动/生成/评分、无重试、无API失败；重新生成10/10 PASS，反馈9/10 PASS，10对help0/harm1/no_change9。1自然家族2对无差异，4人工家族8对中1harm。实测input/output/cache/reasoning和耗时完整报告，不声称等实际token或端到端收益。60次Icarus与1073文件独立核验通过。Windows锁读取收尾失败另记录、仅封存未重跑；旧3880文件/76源码绑定通过。R1c负结果和旧分数保持；本批结束不扩容。

## R3新题族准备完成，尚未执行

[R3准备报告](exploration/20261011/r3/PREPARATION.md)：四个原创新开发机制任务，独立过程Python+手写RTL，固定公开/隐藏数据、24槽共享首次方案计划冻结。28次编译评估/26次仿真：正确与等价编码通过，8目标突变隐藏全检出，公开7/8，保留取消优先级漏检。12组控制测试通过（54mock、0真实调用），新runner安全封存。计划SHA f519bec52af2e1d604a5e91350bfe4acf75bcfdb6da9b6e2ad507e2c1f8eafdc，等待总控实际审阅放行；本轮仅准备，不因轮询启动，不扩大旧题。

## R3正式执行完成：全首次正确，无变化

[R3最终报告](exploration/20261011/r3/RESULTS.md)：24唯一调用/24隐藏评分全部PASS；首次8/8有界正确，两臂各8/8，help0/harm0/no_change8，未启动0，无API/未知失败或重试。仍有天花板，没有自然错误修复样本；四开发家族非独立最终集。32真实compile/sim及975文件核验通过，旧4953文件/源码锁不变。元数据stage冲突导致原汇总exit1，按冻结plan在run外恢复角色/封存，未重跑；仲裁校准收窄为等价实现写法。实际input272882/output8245，费用未知；共享8调用与策略账分开。报告含文献差异和最多三研究方向；本批结束不扩容。

## 新运行器v2离线工程验收完成

[工程审核报告](exploration/20261011/r3-runner-v2/REVIEW.md)：独立版本修复role与judge.stage隔离及EXTRACTION_ERROR两臂保留/配对分类。真实判题字段、多代码块、ASCII/UTF8的128KiB上下边界与完整流程通过；28编译27仿真、25mock、0模型。625新证据/29源码/6771历史绑定核验通过，旧成绩不变。默认代理下两个本地HTTP回归方法失败保留；仅loopback隔离后2/2通过，超长生产prompt传输未验证。24槽新计划已冻结但未执行，仅交总控工程审核，不继承旧放行，不重试403。

## 超长prompt离线CLI补验完成

[补验与v3审核报告](exploration/20261011/r3-runner-v3/REVIEW.md)：原argv12个长prompt实测WinError206，独立stdin新版本完整送达全部16分支及1048609字节混合Unicode压力输入，字节/SHA/nonce通过；退出/超时/输出限制和不重发验证通过。首次夹具WinError183另run保留，历史与v2的7419绑定不变。默认代理34回归仍3failure/1error/2skip，新旧负结果保留，未隔离重试。真实模型/CLI生成/仿真均0；仅本地help/version核实stdin接口，服务上下文未验证。新24槽计划冻结未执行，交总控工程审核。

## R4核心研究问题：离线准备完成，未执行

[R4准备报告](exploration/20261011/r4/PREPARATION.md)：3真正新机制×2重复，层次JSON/信息匹配线性受控意图×实际公开执行反馈/强重新生成，48唯一调用计划、每策略18机会；不称严格等token或自由散文对照。模型意图与RTL/规格三向可观察检查，人工契约仅校准。34来源/8066旧绑定/110nonce核验通过；公开盲点/三个失败校准run/默认代理34回归3failure1error2skip保留。0模型、48槽全未启动，SHA dba616332a6fddd2d04d3def9b632b7fe0c2db8affb2bafe53ce7fdb9dfa87c6；等待总控明确新SHA放行，不执行旧R3准备计划。

## R4有限真实执行完成：再次天花板，无可观察收益

[R4实际结果报告](exploration/20261011/r4/RESULTS.md)：按总控明确新SHA放行完成48唯一CLI回合，12真实意图/12首次RTL/24最终均通过固定隐藏检查，四策略各6/6，12反馈对help0/harm0/no_change12/inconclusive0；三向ALL_MATCH36，没有自然错误或定位分歧样本。JSON/受控线性皆有约束，匹配调用机会不等token，不证明结构化或反馈一般有效/无效。2480新文件/96编译nonce/616544事件/34源码及8066旧绑定独立核验，0 API/未知/未启动/重试。实际input544606 output28679 cached299904 reason5475，feesUNKNOWN。旧题未重跑/成绩不改，默认代理失败和公开盲点保留；本批结束不扩轮。

## R5参考覆盖审计及直接RTL核心消融：仅准备

[R5准备交付](exploration/20261011/r5/PREPARATION.md)：先只读审计参考共源/有限覆盖与不可观察内部规则，再冻结双边沿快照/转义帧/位图分配三个新开发机制。S显式IR→RTL、D直接RTL→无条件再生成，最终统一规格层F/R，48唯一上限/四策略各6分母18机会；机会匹配非严格token或纯格式。18手推状态、三不同推导参考及少量突变校准、48mock控制通过，103编译100sim；两失败校准与default回归3failure1error2skip保留。同作者、无外部独立作者审阅，固定参数binary/#2有界，未证明完整覆盖。33新绑定/110校准源/8066旧绑定/4860 R4seal一致，0真实模型、48槽未启动；SHA752be8b79f544a86f0961ab50e5a8645ea7d18132792670d9373e095fd295b4e，等待总控新审核，不执行旧prepared或自动扩批。

## R5实际中断批次已收尾，不续发

[R5中断报告](exploration/20261011/r5/RESULTS.md)：总控放行精确新SHA后20完整CLI返回、1未知预约、27PENDING，未完成48实验；原turn中断并无关联runner/CLI，run外finalizer禁用生成，仅封存未知及既定隐藏评分，0新调用/重发/补样。20返回样本（3意图17RTL）均有限PASS；四最终臂各2PASS/分母6，反馈4no_change/8inconclusive，只完整双边沿家族，不能推断三族总体收益。未知21 provider消耗不算0，已知input226300/output6156/cached126208/reasoning744，费用UNKNOWN。869run文件/29compile29sim/210223事件、20唯一thread与33源码/2175准备绑定/8066旧绑定/4860R4seal核验；旧成绩/默认代理失败保留。完成即停，供总控审阅，不自动继续27槽。

## R6 离线准备完成（2026-10-11，待总控独立审核）

入口：[R6 PREPARATION](exploration/20261011/r6/PREPARATION.md)。新流式中断记录/保守只读恢复，人工真子进程与计划槽位/父prompt绑定校准；3原创development机制（顺序退休、四拍除法、双流标签join），9专属Icarus检查/3目标人工负例检出，非模型收益。默认34回归3failure/1error/2skip保留，后代树清理UNVERIFIED，同作者/有限轨迹/覆盖缺口明示。41源/16445旧绑定/1398run绑定核验PASS。

仅候选engineering-v2/runner.py及runs/prepared-v2，SHA f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4；48槽未启动、0模型，v1及首次失败留存。未收到总控精确新SHA不得运行；R5不续21/补27，旧证据与成绩不动。准备完成停止供审核，不自动扩批。

## R6 原冻结有限批完成并停止（2026-10-11）

入口：[R6 实际结果](exploration/20261011/r6/execution-v2/RESULTS.md)，只读核验：[analyze_v2.py](exploration/20261011/r6/execution-v2/analyze_v2.py)。总控放行精确SHA f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4后只执行engineering-v2/prepared-v2一次，48clean完整返回、0unknown/0pending/0重发补样；前4production服务gate原证据核对通过。72实际compile/sim、326368事件，2024原运行封存/41源/1491准备/16445历史绑定只读审计通过，原输出/成绩与旧批不动。

6真实IR及42RTL有限判据全部PASS；4臂各6/6，12反馈配对no_change，18S三路ALL_MATCH（复用6IR）。没有自然IR/反馈准确率收益或阶段偏差定位样本，不能推断一般无效/等效；同作者小binary/#2开发域/有界轨迹非最终集/无界/PPA。实际已知input546955/output44818/cache299904/reasoning9716（output内），cachewrite0、半共享账守恒；金额UNKNOWN、非严格token公平。默认回归负结果仍保留。

首版只读审计误设job根目录prompt路径而失败，原源/完整stderr/receipt保存，新analyze_v2仅纠正实际call文件位置，不重跑模型/评分。RESULTS/actual-analysis/closure与新execution-v2封存完成，停止供总控独立核验；不自动开新轮、扩批或重跑R5未知/27槽。

## R7外部候选来源关卡：负向准备已封存（0模型，不可执行）

[R7 PREPARATION](exploration/20261011/r7/PREPARATION.md)：原定12候选完整分母/0纳入，31原来源404932bytes固定2commit/许可/hash/作者/访问与最小适配记录。5逐拍全输出契约不充分、3固定IR域不匹配、2保守近重复、1原ID未核实、1计帧参考规则歧义。2原compile/2sim仅原参考观测，非模型收益/官方测试套件通过：broadcast invalid载荷及reset保留payload可能导致精确判据误报，stat singlebeat byte1/frame0待解；原负结果/失败未修。7HTTP404保留/0HTTP403或重复URL；构包v1路径失败保留、v2只修实际R6适配器路径。0模型/0预约/0自然成绩/0executioncase，无模型prompt/执行plan SHA，不自动换源或改方法凑数。

PREPARATION/PROTOCOL/SOURCE_MANIFEST/REFERENCE_AUDIT/COVERAGE/SPLIT与候选、历史排重hash、访问适配/原日志/失败/method lock齐备。seal-verification PASS_NEGATIVE_PREPARATION_INTEGRITY：19971旧绑定/7固定方法/71新packet绑定及精确file set一致；packet SHA b2f63e5db433bc0a099574b65ecfffec30c787141741b11b3cb0126414cf506e。此SHA只审核负向准备包，不能放行模型；完整覆盖/可靠执行参考关卡未通过，不称方法无效或作者全局bug。已停止供总控核验，若改握手/IR/方法则接触并影响改动的候选须降为development另立新准备。R5沿用原验收，不重发21/补27；R6/学校/旧证据成绩与default回归失败保持。

## 握手事务判据独立开发v1：仅离线校准交付

[RESULTS](exploration/20261011/handshake-dev-v1/RESULTS.md)：新source-plan/逐consumer事务FIFO/stall保持/有界fair drain checker，与R6/R7原逐拍判据隔离。22手推trace（7合法PASS/11人工FUNCTION_FAIL/1输入违规/3TRACE_INVALID）和10手写native RTL配置（3合法PASS/7人工FUNCTION_FAIL），全部预声明匹配；0拍/3–5拍合法延迟、invalid data/last变化或X通过，loss/duplicate/order/data/last/stall-valid等检出，source永远ready0不成空账PASS。10真实compile/10sim和136run/7source绑定，3unit tests复用见证不算新独立设计；没有自然模型收益。

默认required3module只一次24tests：3failure1error2skip/exit1（local mock transport RemoteDisconnected及0observed，原因未定），原日志/失败保留，不隔离重试或改代理。固定2consumer/8bit+last/single clk/80cycles≥8fair drain；native初始sync reset，中途取消仅手推语义，非无界或完整AXI。source/期望/RTL/audit同作者，flat ledger不同抽象交叉核验不称外部独立作者。0模型/0候选扩充/0旧RTL评分/0production integration，R7原包及旧成绩保持；受此方法开发影响的接触来源以后须作development。

seal-verification PASS_DEVELOPMENT_CALIBRATION_AUDIT：20065历史/R7保全，7source/136校准/160新packet绑定精确集合一致；packet SHA d060a32dba45329046e7a71cf5b3c687fccc874bbaede47415bad3d3c9de268a，execution_plan_sha256=null，不作模型放行。CONTRACT/PROTOCOL/COVERAGE及全部人工负结果/default回归/原stdout-stderr/receipt/read-only audit齐备，完成停止交总控审核后再决定下一步。

## 2026-10-11 handshake-dev-v2 有限离线补验与意图设计（待总控审核）
新包：[RESULTS](exploration/20261011/handshake-dev-v2/RESULTS.md)、[比较设计](exploration/20261011/handshake-dev-v2/INTENT_COMPARISON_DESIGN.md)、[seal](exploration/20261011/handshake-dev-v2/seal-verification.json)。8手推4PASS/4FUNCTION_FAIL；8native5PASS/3FUNCTION_FAIL，8compile/8sim、640采样。原预声明类别1项不符保留（shared reset残留实际UNEXPECTED而非DATA_OR_ORDER），校准exit1、不重跑；完整条件15/16，状态16/16。旧默认24回归exit1保持未重试；旧20231、新源8/run90/包113绑定核验，checker与v1相同。packet SHA c614a32526e2fa0cb182be7b9dde7aca6e6249df54169a2b190da1f5569eaf16，审计exit0但校准负结果不抹除。真实手写RTL中途reset、因果与不同合法缓冲有限补验；人工开发不算自然模型效益。6比较例仅DESIGN_ONLY/NOT_VERIFIED，旧IR域不足。0模型/0来源或候选扩充/0生产接入/0旧评分重判；R7与v1保全，交总控后停、不自动进入外部保留任务。

## 2026-10-11 v2 IR依据独立补正（design-addendum-v1，待审核）
[补正说明](exploration/20261011/design-addendum-v1/CORRECTION.md)必须与v2原设计并读：原文把旧fsm_ir单bit Moore当当前IR依据的推断撤回。只读源锁确认prepared-v2→engineering-v2/runner→r6/runner→r6/intent/tasks/judge；当前R6是最多16个1..8bit寄存器+表达式域，有限广播潜在可表示，但完整映射UNKNOWN、事务采样/driver/意图关系NOT_VERIFIED。原6例末例仅旧FSM域例，不代表当前R6不能表达。0新IR/compile/sim/default/model/候选执行；原v2 packet及117文件保持，原校准exit1和默认exit1保留。新补正8包绑定/162原源绑定，packet SHA 090fa59f73bc8355a52d15fc7158e368a6fa94e7c6355a962c4043baf975f012。新source-snapshot带SHA/精确行，audit+seal只读hash/set，DESIGN_ONLY。提交总控后停，不新增离线轮或放行生产模型。

## 2026-10-15 transaction-alignment-v1 阶段A冻结（未执行，待总控审核）
[协议](exploration/20261015/transaction-alignment-v1/PROTOCOL.md)、[相位/对齐](exploration/20261015/transaction-alignment-v1/SAMPLING_ALIGNMENT.md)、[手算预期](exploration/20261015/transaction-alignment-v1/REFERENCE_HAND_DERIVATION.md)、[状态](exploration/20261015/transaction-alignment-v1/PREPARATION.json)。精确plan SHA c2aeef0482f72c1deded6bf45d6aae6012a889dc4f71801a633e4aa04e942c10；24新源/20354旧绑定，静态JSON/AST及哈希检查完成。12配对描述、11拟执行、1spec含糊不执行，意图预期6PASS/2FAIL/4NOT_EVALUABLE；不是观测成绩。完整3reg当前R6 IR JSON、独立新task overlay、一处yield流式插桩、PRE/POST TB、offer/epoch取消账与不同合法结构均只准备，映射与插桩功能尚未验证。阶段B精确11IR/11compile/11sim、80周期、并发1、1800s/250MiB，需总控先审采样与适配并绑定此SHA一次放行；异常停止不补样/重试。当前IR/compile/sim/default/model均0，run-v1不存在。旧v2 c614...、补正090...、15/16类别负结果/exit1和默认负结果保持，0来源/候选扩充/生产改动，fyp自动化仍暂停。交总控一次后停止，不自动准备外部任务。

## 2026-10-15 transaction-alignment-v1 阶段B完成并获总控独立验收
按精确plan c2aeef0482f72c1deded6bf45d6aae6012a889dc4f71801a633e4aa04e942c10执行一次，exit0，实际11IR/11compile/11sim、无重试/模型。完整12描述中11真实执行+1case10预声明未执行，不把skip当检测。实际IR10PASS/1INPUT_PROTOCOL_FAIL；RTL7PASS/2FUNCTION_FAIL/1INPUT_PROTOCOL_FAIL/1TRACE_INVALID；意图6PASS/2FUNCTION_FAIL/3NOT_EVALUABLE。原native1760事件/IR1760事件、同构320PRE/POST身份一致；提前消费sink3/source7、跨epoch残留检出，合法差异通过，reset集合差异按NOT_EVALUABLE。
[运行后报告](exploration/20261015/transaction-alignment-v1-report/RESULTS.md)，独立报告目录封存、原run-v1的270证据锁不动。run evidence SHA a22112bedb7c181f9fde4d1cee957351fa5fcd9077b30fde0c75a44fd1dda699；报告packet SHA c491b93fe9eb625610e1c4cb8c554fac5c75d16e3ccbfb12d8e849032eea9da1（6报告绑定/298执行准备文件绑定）。24准备源/20354旧绑定保全，原v2和default负结果保留。
总控独立完成回执：[completion audit](validation/fyp-exploration-review/transaction-alignment-v1-completion-coordinator-audit.json)，ACCEPTED_FINITE_DEVELOPMENT_TRANSACTION_ALIGNMENT；另写闭式IR与独立事务账核原轨迹，无重跑。条件结论：具备另行有界准备新外部来源/契约盘点的有限基础，尚未授权启动该准备或模型；无通用映射/未插桩run等价/自然定位效用证明。新报告自检仅同作者只读核验，不代替总控。完成停，不重跑/不派生下一轮/fyp保持暂停。

## 2026-10-16 固定输入 RAG / 无RAG 统一准备（冻结，执行阻断）
入口：[准备摘要](exploration/20261016/fixed-input-rag-v2/RESULTS.md)、[协议](exploration/20261016/fixed-input-rag-v2/PROTOCOL.md)。5原开发题×3指定模型×2条件×2样本=60待审槽位，替代单条件30提案，非90；0模型/embedding/rerank/训练/EDA。资料1来源18有效段，BM25固定检索；初版19段过滤失败与CRLF/UTF8准备失败保留。三模型同题同条件拟发送消息一致，实际服务包装未验证。22,358旧文件hash无变化；40资产/115源/30payload/60slots/检索离线验收PASS。状态PREPARED_BLOCKED：路由/共同硬token cap/隐藏包装、当前Yosys、正式执行器及request_delay歧义未解除。无扩批、补样、旧分数重评或自动化恢复。
精确plan SHA a5ad53689820640e833845fde3366d1f6f9318d98db6efbbccd35b9acd73dff8；packet SHA 47603eb9e0c0fa6c76d0fa3ea7d4ca7ab2ffdadb880140a7b3dee03dce030a5e（118文件，另2封存元数据）。原单条件中间包SHA 9838a2b05b7fd97fd63870568051a4a4fd485fd7f0e85c4e3acff2c6e8012ed4保留并绑定。完成后停，由总控读取独立审核；不反向跨chat派发，不构成执行放行。

## 2026-10-16 公开上游原题 RAG 准备（冻结待总控及用户审阅）
[两题完整原文/固定来源/中文理由](exploration/20261016/public-benchmark-rag-v1/SELECTED_QUESTIONS.md)、[原始数据转发包](exploration/20261016/public-benchmark-rag-v1/public-originals.zip)、[摘要](exploration/20261016/public-benchmark-rag-v1/RESULTS.md)。官方NVlabs/verilog-eval commit c498220d0a52248f8e3fdffe279075215bde2da6，19题57原始文件/61上游文件，Git blob+SHA校验。限定分层/保守近重复后条件选2（Prob018_mux256to1、Prob095_review2015_fsmshift），目标缺3不补，实际待审24槽；旧60槽方案不执行/不叠加。18段通用RAG资料复用，原prompt原字节，system包装单列，0模型/embedding/rerank。
探索原参考别名校准1次编译失败、0仿真/0SAT，保留且停止。总控另4探针+1原文件编译支持COMSPEC/系统PATH环境根因，原3源和argv一致时补COMSPEC编译成功；只读引用20诊断文件，不重复跑。总共6编译尝试、0sim/0model，不证明独立正确性。新SAT14/32和31事件仅静态设计，组合复位N/A；12payload/24slots与原文汇总验收通过，22358历史+217旧准备文件无hash变化。两题检验力弱，不声称公开库只有2题可用或代表多样设计。
plan SHA034a76616615cba71e0045d63f7a50dabe30424aea6179cba3ca75b169a2ea31；packet SHA8a3b613cf353d40f346bc12ffcb9880461218d53a8984083cd3d506f00f039e6（155文件+2封存元数据）。状态PREPARED_BLOCKED：先总控核验，再由用户明确确认选题与方案；仅总控通过不自动执行。服务包装/硬token cap/模型支持、完整执行器/当前Yosys/增强校准阻断继续保留。冻结后停，无逆向跨chat消息，无扩批补样/学校任务/自动化恢复。

## 2026-10-23 正式评测 / RAG 调优隔离规则同步
[探索侧规则补充](exploration/20261023/rag-evaluation-boundary-v1/BOUNDARY.md)。正式评测前冻结语料/分段/检索算法及参数/停用词同义词/top-k排序/包装预算；可按原题自动检索，但不得依据正式评测题或其检索/答案/评分针对性改进。若据观察调整，另建版本并将涉及题标development/已暴露，后续独立评测换未参与调整的题且先审核，不自动筛题扩批。仅审阅报告不是方法修改。Prob018/Prob095均记reviewed；本次未改方法。基础设施修复和RAG调优分账，不借修复改题/评分/检索。旧公开包155文件hash核对无变化，原检索/失败保全；新增模型/检索/筛题/EDA均0，用户确认前不执行。共享规则由总控维护。

## 2026-10-23 当前正式结果资格同步
[探索侧引用边界](exploration/20261023/experiment-eligibility-sync-v1/REFERENCE_POLICY.md)，权威口径为[总控纳入清单](validation/EXPERIMENT_ELIGIBILITY_20261023.md)。八项旧实验均不计当前正式模型效果；人工校准仅工程附录，R1b/c带IR或多阶段来源排除；R2/R4及R5/R6最终流水线不计当前单次对照。Dev10、R3首次及R5/R6 direct_first子集因未逐条核清暂排，不宣称每条均违规。当前已确认可纳入的新规则已完成模型结果为空，非0%通过率。RAG仍0模型、两题reviewed，未发现据两题已调RAG证据，不捏造泄漏。旧正/负/无变化/未知证据一并保留，不物理删除或倒改；后续引用不以历史数字包装合规收益。本次仅规则说明，无新实验/补样/模型/EDA/检索。

## 2026-10-23 新轮公开RAG A→B→C准备封存（待总控/用户审核）
[原题、来源、理由和实际检索](exploration/20261023/public-rag-holdout-v1/USER_REVIEW.md)，[计划](exploration/20261023/public-rag-holdout-v1/plan.json)，[静态审计](exploration/20261023/public-rag-holdout-v1/audit.json)。A30源先冻后读新题，SHA c0609d940a0e586e2b7b5fc81ca6d58bd1eeee5e1d4cecbe40415317f341ead1；B固定20候选60原文件，12合格8排除，前5为Prob089/023/146/032/064，B锁4505a697f76ef3fdbf16a0bfd80e466af3a4c99be4bf7588e1fecf00d118d973；封B后才做5次离线词法检索，C锁b6c8e23341793042fd5f7e17d84a1fa1465a83887c5e82e8d610f9767fbcde02。未因新题调整A，弱相关case/latch片段保持；资格为静态条件性判断，串行stop恢复、复位输出、拼接列举顺序仍请总控核。10组同条件消息/60拟请求全部NOT_STARTED；0模型/embedding/rerank/compile/sim/SAT，0下载重试。完整包210绑定，packet SHA9e14e8f0b53b6bc81caee003c01bf45b6cc4bae17170ac98259511866957be27；plan SHA69f0537f247b3c2913695c19ba7608f89ec625d66bd26b95269a3dc5c5b6b447。旧155/118文件包、97基线及22复用绑定核验保持；默认exit1/v2 15/16负结果保留，不重跑。真实包装/硬token上限/模型路由/执行器/额外验证仍阻断；旧批不叠加，自动化不恢复。先总控再用户确认，不自动执行或回填候选。

## 2026-10-23 全部固定20题执行补充包（已校准，模型技术阻塞）
用户新授权覆盖旧B全部20题、三模型×两条件×两样本=240槽，替代旧60/24方案、不叠加、不另筛。入口[状态与阻塞](exploration/20261023/public-rag-all20-v1/STATUS.md)、[全部原题与实际检索](exploration/20261023/public-rag-all20-v1/ALL20_REVIEW.md)、[审计](exploration/20261023/public-rag-all20-v1/audit.json)。A30文件原字节复用，原60源不改，旧5检索逐字复用、另15固定自动检索；全20原排除/歧义/历史标签保留，总控三项后续歧义裁决单列，清晰子集仅Prob023/032的24槽且包含于240。先封448源pre-execution SHA2097ea04c4a454b7b3a571ddb5be1be078a3eebe65d502a71d3b46a7699922ab，再实际20compile/20sim工具校准全部正常，6425原样本零差异，无重试；同RefModule别名一致不是独立oracle或模型成绩。原默认/v2/旧包负结果不改。CLI0.163.0-alpha.11.1 ChatGPT已登录但三个ID支持/共同硬8192cap/实际包装未核；API配置只有demo/禁用占位、无真实目标凭据。240拟请求全NOT_STARTED、模型/未知/403重试/学校动作0；有限生产dispatcher尚未实现，不冒充可执行完成。只待技术门槛与总控核验，不重复申请同一测试意图。752文件完整包SHA72094112b5c0f6b72e920ad8d362c78ee5e302ee758b1e2de90c7c120b062d39，自动化保持暂停。

## 2026-10-23 有限执行器基础设施完成（真实接入待配置）
[状态](exploration/20261023/public-rag-executor-v1/STATUS.md)、[最小配置](exploration/20261023/public-rag-executor-v1/SETUP.md)、[审计](exploration/20261023/public-rag-executor-v1/final-audit.json)。独立core/http_once/dispatch实现固定240槽持久预约fsync、单账本排他、无重试、403/未知停机、完整返回与未知分开、准确payload与8192预算、128KiB提取及EXTRACTION_ERROR阶段保留、原测试适配。第一轮27项1长路径夹具error保留及源码快照；缩短job目录后27pass，新增中断与落盘返回保护后29pass；另5放行门槛检查通过。全部为offline transport/EDA mock，实际模型/HTTP生成/本轮EDA/参考校准重跑0。原all20 752文件包保持。官方文档和本机目录核3准确ID，API supported元数据不等于账户权限；CLI共同输出cap未获正式证据，不读auth/token、不调用私有接口。新生产dispatcher不再缺失，当前route/credential/technical-release缺失，初次preflight阻塞，0预约/0未知/240未启动。runtime为后续操作区，排除于静态packet；冻结1928文件packet SHA f6d2b74252004dcc89239f184c0465ebb865d5c3662b6a25d891d520468e9e17，source-lock SHA5e8ae122274e4b0eb75d620a38be09a36ca9c8b40416a138b3e19ab6c1709297。总控核验真实接入、参数与可观测消息边界后再放行；不重问20题测试意图，不扩批或恢复自动化。

## 2026-10-23 已登录CLI可用性与协议能力核查（无生成）
[结果](exploration/20261023/cli-cap-v1/RESULTS.md)。本机目录存在准确luna/terra/sol且supported_in_api=true，不等于推理权限实测；官方model/list也可能用内置/缓存目录。3个非生成命令保存版本对应452 schema/help，空隔离CODEX_HOME，不复制/读取auth/token、不请求HTTP中转、不启动app-server/RPC/thread/turn。ThreadStart有instructions/fallback控制入口，但TurnStart无直接completion/requestcount硬cap；452schema对应字段搜索0命中，provider capabilities仅imageGeneration/webSearch。不能据任意config键或10000truncation声称8192输出cap。原协议单推理/角色包装/共同硬cap仍未证，原1/3/5序号的每模型一个槽仅列计划未预约，0生成/0usage观测/240未启动；不改RAG/原题/模型/预算。原API401未重试。GBK读UTF8元数据失败保留后改显式UTF8完成，不重跑生成schema或校准。旧all20 752绑定保持；新470文件packet SHA a4d8dd6d31d616597194fcb64261aece212ee8ee02e70fa88ed4908e73648de0。


## 2026-10-28 控制台v3独立验收与30候选冻结（待用户审核，0模型）
[总控独立报告](validation/rag30-independent-review-20261028-v1/REPORT.md)；[完整原题、来源、风险及实际检索](exploration/20261028/public-rag-30-review-v1/USER_REVIEW.md)；[36槽主候选清单](exploration/20261028/public-rag-30-review-v1/console-package-main36.json)。30分母=3主/22辅助/5不执行，建议36槽，300草案仅归档，不自动扩批。48段RAG与原提示原题不改；30参考自比不是独立oracle。874文件已独立核验，无release。
