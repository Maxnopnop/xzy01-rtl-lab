# v2 设计依据补正（2026-10-11，DESIGN_ONLY / NOT_VERIFIED）

原包 exploration/20261011/handshake-dev-v2，SHA c614a32526e2fa0cb182be7b9dde7aca6e6249df54169a2b190da1f5569eaf16 不修改。本补正修正文档依据，不修改原RTL/checker/实验、期望或分数，不执行IR、模型、编译、仿真、默认回归。原8手推/8native、shared_reset_stale预声明类别不符导致校准exit1，以及旧默认回归exit1均保持。

## 原引用与错误影响

原 INTENT_COMPARISON_DESIGN.md『现有表达域』及『三路关系和对齐条件』第1项，将根fsm_ir.py的1bit Moore不足作为本轮IR不可执行的主要依据；RESULTS.md『设计、保全与尚未证明部分』也据此说“旧IR表达域不足”。这些对 **旧FSM研究模块** 的源码事实正确，但没有追踪当前R6四臂的真实调用链。把它当作当前R6 IR域依据不成立，本补正明确撤回“当前IR因为仅1bit Moore所以本任务UNSUPPORTED”的推断。原文件保留为历史错误，后续阅读必须同时使用本补正。

原 semantic-examples.json 最后一例 legacy_ir_domain_gap 的 ir_schema 明确是 fsm_ir.py/schema1/1bit_Moore，作为旧FSM假想广播例仍成立；不能代表当前R6 intent不能表达。原6例不改、不增加新例；本补正中的替代适用解释为：当前R6广播表达能力 **UNKNOWN / 映射未验证**，生产任务未配置，意图比较 **NOT_EVALUABLE**，不是已证明UNSUPPORTED。

## 已核实的源锁与调用链

prepared-v2/plan-lock.json绑定plan SHA f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4；plan.json.source_hashes绑定engineering-v2/runner.py以及r6/runner.py、intent.py、tasks.py、judge.py等实际源。本补正 audit.py 只读验证全部源hash及preparation-lock，记录具体匹配值，不导入runner或执行score。

- r6/engineering-v2/runner.py第4–7行将BASE设r6，导入r6/runner.py的core，并将core.RUN改成runs/prepared-v2；9–14行在core.hashes中追加engineering-v2源绑定。
- r6/runner.py第6–8行把r6置模块搜索首位，import tasks,intent,judge；不是根fsm_ir。第103–109行，私有rows由当前task资产读取，intent角色调用intent.check；RTL_spec由judge.simulate，结构化RTL的intent_spec来自intent.check，RTL_intent把相同事件rows的expected替换为IR逐事件values再judge.simulate。
- r6/intent.py第49–63行的parse通过tasks.TASKS[task]绑定输入名及输出键；因此语言一般能力与当前已配置三任务必须分开。现TASKS仅ordered_retire/restoring_divide/tagged_join（tasks.py第4–7行），没有本广播任务。当前原封存配置不能直接以broadcast任务运行，不能借用三题输出绑定冒充事务校准。

完整原文、原文件SHA和精确行号见 source-snapshot.json；这不是新来源下载，也不是新的模型调用。

## 两个IR域及事件语义

| 项 | 根fsm_ir.py（旧FSM模块） | r6/intent.py（当前R6） |
|---|---|---|
| 状态 | 1..32命名Moore状态、单bit输出 | 1..16命名寄存器，每个1..8bit |
| 输入/输出 | 输入0/1、单bit输出 | 名称/位宽来自tasks.TASKS，输出键必须完全对应；当前三题具有多bit端口 |
| 转移 | 每状态每输入一条，posedge | next_rising/next_falling完整不相交寄存器组 |
| 表达式 | 状态转移表、无通用载荷表达式 | 0..65535整数、寄存器/输入名、加减/位操作/常量0..7移位、比较、and/or/not、条件式；无eval/exec |
| reset | 元数据sync/async、active0/1 | async_low/sync_low/none，寄存器reset常量；隐式rst_n |
| 判据 | 有限抽象Moore product_check；另timed_vectors | check比较run的每事件打包输出与row.expected，无独立事务对齐 |

r6/intent.py第65–75行：state先用reset值初始化，last clk初值0；每row根据clk与last是否不同选择边沿bank，async_low低reset每row清状态；sync_low在**发生边沿时对该bank**的寄存器应用reset，故若采用本次仅posedge同步reset映射应把所有目标寄存器放next_rising、next_falling为空，不能假设sync_low自动统一只在posedge。边沿更新所有表达式使用该边沿旧state构成的env（不会因同循环先更新寄存器给后表达式新值），按各寄存器width掩码；随后用更新后state和当前输入评价outputs并打包，稳定clk也计算组合输出。它不是局限Moore。

judge.py第13–26行按task输入/输出顺序打包完整向量，每事件同时赋clk/rst_n/input，等待#2后比较RTL输出与expected。这与intent.run的更新后输出模型对应；v2 pre-edge握手采样不能直接拿这些post-event values在同edge作事务接受判据。适配至少需要明确低电平输入设定后/上升沿前采样、posedge后的状态更新、组合路径、reset行排除，以及现有row驱动策略如何保持未握手输入。当前run API只给打包output列表，不给source接受/offer_id/取消账；不能仅换expected数组宣称事务域意图比较实现了。

## 本广播是否潜在可表示：只读审查结论

单时钟、8bit data、last、两个pending标志、sync reset：潜在可以用一个8bit数据寄存器、1bit last、两个1bit pending（或一个2bit pending）在R6预算内描述one-slot广播，输出表达式从state和input计算ready/valid等，宽度无明显根本障碍。active-high rst需映射到隐式rst_n的反相驱动/契约，必须定义而非改旧源。

深度2独立消费者队列也有潜在有限寄存器空间：4个8bit槽、4个1bit last、4个1bit读写指针、2个2bit计数=14寄存器，低于16。语言没有数组访问/辅助表达式节点，但两槽可以拆成命名寄存器并用条件式选择，旧state next表达式可描述同时入出。这个预算草案不是完整schema映射，也不证明所有表达式长度/AST预算（每式4096字/512节点、总JSON16384 bytes）、名称约束、组合依赖、output keys/位宽、采样和reset语义都满足；容量更大或其他结构亦不能据此判可用。

没有创建/解析可执行broadcast IR，没有改TASKS/资产/judge、扩IR域或重跑校准。因此语言一般潜在表达能力不能等价于当前冻结任务可直接运行；也不能因当前三题未含广播就证明语言不可表达。总体状态：**潜在表示空间存在；完整可执行映射与验证UNKNOWN；事务域集成NOT_VERIFIED**。

## 仍成立的比较设计与验收边界

v2设计的同外部驱动策略/offer_id、各自source接受与consumer交付cycle、背压承诺、reset取消账、允许stuttering、不同reset接受集合ALIGNMENT_NOT_EVALUABLE保持有效的设计要求。当前R6 RTL_intent仍按同事件全端口输出等式，不是这些新关系；无生产事务driver、解析适配/独立参考及三路分类器，所以IR_spec/RTL_spec/RTL_intent事务关系未验证。六个语义例仍仅手工设计，原前五例是假设适配执行器后的关系，不冒充当前R6执行结果；第六按上文修正范围。

验收项仅：①实际prepared-v2计划与源锁一致；②调用链与parse/run/judge采样有精确行证；③两个IR域分开；④潜在映射和UNKNOWN分别陈述，不证明不可用/可用；⑤原v2完整包和封存元数据保持；⑥0新执行/候选/来源/模型，默认与新校准失败不抹除。本补正完成即停交总控，没有新离线轮或外部保留任务放行。S关系不代表内部理解因果，D无IR不猜阶段，私有意图诊断不向F泄露的公平性约束不变。
