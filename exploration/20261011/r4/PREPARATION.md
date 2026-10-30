# R4离线准备交付

仅准备完成，真实模型调用0，48唯一槽全部未启动。执行入口runner_v2.py；冻结SHA256 `dba616332a6fddd2d04d3def9b632b7fe0c2db8affb2bafe53ce7fdb9dfa87c6`。等待总控对本SHA明确放行；不执行R3/v2/v3旧题计划，旧实验/成绩不改。

## 问题与因果比较

R3无模型中间意图，首次8/8通过，不能支持结构表示/反馈减少自然错误。本轮在新机制中记录模型IR对规格、RTL对IR、RTL对独立规格三向状态，同时匹配设计事实和阶段机会。

S=层次JSON契约，L=线性受控语言；各有F=公开执行反馈、R=无反馈重新生成。L仍有固定句法，主张仅限组织/序列化形式，不能推广为结构IR对任意散文的优势。自由散文需主观解析或额外转译，人工正确IR只能校准，均未混入主臂。

每例S/L各由真实模型生成意图，再由模型实现首次RTL；各表示F/R共享各自意图/首次RTL。最终两臂规格、公开例子、原意图、原RTL、指令相同，只有F增加实际公开三向检查JSON。R允许纠正/替换候选，是有竞争力的重新生成基线。表示比较S-R vs L-R、S-F vs L-F；反馈比较各表示F vs R。反馈本来增加执行信息，不能称四臂字节信息完全相同；表示对照设计事实和非反馈上下文匹配。

## 调用图与预算

|阶段|每例唯一调用|六例唯一调用|共享关系|
|---|---:|---:|---|
|S/L意图|2|12|各表示F/R共用|
|S/L首次RTL|2|12|各表示F/R共用|
|S-F/S-R/L-F/L-R最终RTL|4|24|独立一次，无补样|
|合计|8|48|每策略18机会，实际不能算72|

三族各2重复；每策略18机会，半共享分摊各12调用，总48。完整部署视角含全共享费用各18另报，不能求和为实际账。actual input/output/cache-write/cache-read/reasoning、缺失null、字节/时延保存；实际账只加唯一调用。未知预算预留不当零成本、不重发。

同gpt-5.6-sol/low，串行，180s/调用，10800s派发窗口，750MiB派发前磁盘阈值，48上限；前4实际调用返回且无基础设施失败的服务门槛，不按格式/功能成绩择样。任务/表示/分支顺序预先交替。prompt256KiB、intent解析16KiB、RTL提取128KiB，响应先完整保存后判，超限/格式/unsupported/INPUT_LIMIT保留。CLI服务token上限未验证/不能强制，字节限制不是服务token约束：匹配调用机会，不是严格等token/等算力。详见budget.json、PROTOCOL.md。

每策略主分母固定6，报PASS/6及失败/未知/API/PENDING；两表示各6反馈对，未完成inconclusive。保留12意图、12首次RTL、24最终RTL。可解析IR子集、已完成子集、实际token效率和逐族结果只作敏感性分析，不替换主分母或证明等token效果。样本小，不估可靠显著性。

## 新任务与参考

epoch_commit：双银行stage/同边沿原子提交/abort优先；refund_credit：退款先饱和再带权购买/零cost拒绝/组合预测；tagged_join：双流新标签先替换再匹配/XOR/flush优先。不是R1/R2/R3重跑或改名；相似性、作者/共源风险和9手推见证见TASKS_AND_REFERENCES.md。仅开发集，非最终集。

文字/接口/seed、公共61/56/46事件、隐藏6625/4720/14290事件、过程Python和手写RTL及资产锁冻结。过程oracle不从IR/RTL生成，RTL不从契约转换；同助手作者/同规格仍有共源误读风险。calibration_contracts仅人工机制校准，不进执行prompt/主模型分母。执行模板prompts.py锁源，12个初始具体prompt在prepared-v2/prompts；templates是解释性导出，非另一个执行源。

## 支持域与定位

二值单时钟rising/falling及async_low/sync_low/none；1..16无符号1..8位寄存器、并行旧状态next、组合输出及有限AST条件表达式。支持多位状态/计数/缓存，不支持任意代码执行、调用、层次、多时钟/四态等；格式EXTRACTION_ERROR/IR_INVALID、域外UNSUPPORTED保留，不修成正确IR。完整限制见intent.py/PROTOCOL。

分别记录IR_spec、RTL_spec、受支持时RTL_intent；无效IR则NOT_ASSESSABLE。最终只重新实现RTL、不重写意图，能观察纠正/绕过意图，不能称意图修复率。BOTH_DIVERGE及其余类别是三路可观察关系，不能唯一归因内部思维/因果传递。反馈最多8条公开差异，不含隐藏参考、状态、数据。

## 校准、工程验收与原始证据

calibration-v4：15编译评估、14Icarus，正确路径全通过，三个核心突变公开/隐藏3/3检出；额外满额退款cost1突变公开PASS、隐藏FAIL，漏检冻结保留。15意图执行检查、7格式/域外负例、9手推见证通过。v1/v2/v3失败及源码快照保留：参考局部tb被策略拒绝、JSON tuple/list比较错误、突变重引tb策略拒绝；规格/事件未改，校准失败不是模型成绩。

control-v1完整48槽固定夹具使用真实IR/RTL解析/Icarus和判题字段；80编译、78仿真、11组通过。验证表示事实/反馈唯一差异、非法意图及多代码块首次两臂继续、role隔离、固定分母/共享费、预算/源码停止、unknown/API不重发、INPUT_LIMIT/PENDING与持锁封存。49mock（48完整流程+1 API错误）不是研究样本；人工2help/2harm/8no_change仅验证配对代码。

原R4 runner的unknown摘要未标保守预留，可能把未知已启动数报0。保留其源/完整流程run，新runner_v2仅修正未知预留会计、准备门槛和新路径；unknown-v2保留差异。针对性测试1 UNKNOWN_INTERRUPTED、47 PENDING、started1，四策略仍6分母，0 callback/仿真；未重跑不变的80编译流程。model_called字段为保守预算预留标记，不等于确认provider调用；未知/早期auth错误时服务是否开始不可确定。

verification.json独立核验PASS：34来源、48角色/raw、48未启动槽、证据锁/110仿真nonce/9资产与模板锁；8066旧证据/来源绑定核查记录。R4保留113编译/110仿真（含必要失败版本，不含仓库回归临时夹具）；旧题/历史模型RTL无重判，旧成绩不改。

按AGENTS运行原34回归，默认代理未改：3 failures、1 error、2 Yosys环境跳过，两个loopback方法仍失败；regression-v1完整日志独立封存，无代理隔离或失败循环重试，不报全回归PASS。

## 未验证清单与下一实验

只读复用v3 stdin adapter/process，SHA纳入本计划；真实Codex stdin生成/服务context未验证，离线运输夹具不是服务证明。未来前4服务门槛仅在新SHA明确放行后执行，失败即停，不周期重试403或扩大样本。

没有硬服务token上限；磁盘是派发前阈值，非OS硬隔离；IR有有限语法/数据边界，没有独立CPU墙钟隔离。模拟每次compile15s/sim10s。既有kill_tree前批仅确认直接进程结束，后代树清理未独立验收。没有综合/PPA、最终集或无界正确性结论。

原文文献核查/差异见LITERATURE.md，工程修复不当研究贡献。下一有区分力实验仅是审核后冻结48槽：观察自然模型意图/RTL偏差及四策略固定分母结果；若首次全正确，保留天花板，不事后加题/扩轮追求收益。
