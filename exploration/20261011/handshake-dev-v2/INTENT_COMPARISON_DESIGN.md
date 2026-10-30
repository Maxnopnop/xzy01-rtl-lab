# 事务域 IR／RTL 意图比较：DESIGN_ONLY / NOT_VERIFIED

## 现有表达域

本地 fsm_ir.py 的 SCHEMA_TEXT/parse/trace/product_check/timed_vectors 已查读并纳入prior锁：schema1、posedge、Moore、1bit输入及1bit状态输出、1..32状态、sync/async reset元数据；每状态恰两条0/1输入转移。其product_check证明有限抽象Moore图从reset的关系，timed_vectors按边沿前/后值；没有8bit载荷、last、source/consumer ready、双消费者、队列、事务身份或取消事件。不能把该解释器输出冒充本广播任务的 IR 握手轨迹，不能更改域来强凑题。本设计没有新增IR解释器或RTL_intent生产判题；6例仅手工语义草案，不是端到端集成测试。

## 输入实验与事务身份

外部计划固定输入offer序列、每笔offer_id（epoch,ordinal）、载荷、last、驱动策略、reset日程及每消费者ready日程；来源哈希不由DUT决定。相同驱动策略指“上一笔握手后才推进下一笔，未握手保持valid与payload”，不保证在不同ready实现上有逐拍相同s_valid/data；如果强制相同波形，可能对某实现违反source稳定，应标 INPUT_PROTOCOL_FAIL / INCONCLUSIVE。

每个执行对象单独产生 pre-edge 采样：reset transition/epoch、offer_id、source接受(cycle,payload,last)、每consumer交付(cycle,payload,last)、stall承诺及取消pending/unaccepted账。offer_id来自独立驱动器记录，不从输出载荷猜身份；重复载荷也按接受次序绑定，consumer ordinal在各epoch单独递增。输出只可关联该实现已经接受的输入，source_cycle<=sink_cycle（允许等号），先用该实现本身的时间因果/背压判据；无效payload不比较。不能事后配对一个提前输出到将来输入来消掉错误。

## 三路关系和对齐条件

1. IR_spec：仅在预冻结且表达域适配的IR执行器、独立公开规格判据可用时，对IR本身执行该事务契约和bounded完成义务。旧schema在本任务为 UNSUPPORTED_DOMAIN，不能给PASS/FAIL。
2. RTL_spec：独立激励和规格事务判据。当前v2仅人工有限开发验证；真实生产轨迹的解析/driver_id接入、参考独立性、IR执行器仍未完成。
3. RTL_intent：先核对域、采样相位/reset定义、驱动策略及完整轨迹，再核对同epoch实际接受offer_id集合、取消集合及最终公平完成边界。相同可比接受集合时，对每consumer比较(offer_id,payload,last)有序交付关系以及各自合法时序义务；允许空闲/stuttering和不同握手cycle，不要求微架构信号一致。任何一方因果/背压破坏不能因最终序列相等而PASS。

若固定时间reset发生时两实现因为ready不同接受集合或部分已交付/取消集合不同，则对每实现分别做spec检查，可都合法；RTL_intent需标 ALIGNMENT_NOT_EVALUABLE（附具体集合），不能判实现错误。可另行预声明输入停止且两边完全drain后共同reset的driver策略，取得相同episode输入集合；不能看到结果后移动reset或补题。按事务数触发reset亦需定义外部协调器、共同结束条件，不能在两边任意选各自reset导致比较不同问题。无reset时最终完成相同offer集合才允许时间消去；若到窗末任一未接受/未完成则是有限spec义务失败或适用性不足，不能无限延长直到PASS。

IR_invalid、工具错误、未知控制、source违规、域不足或无法对齐都独立保留，不能归入FUNCTION_FAIL收益。即使两方同样错并有相同序列，只有两方因果/背压义务都成立才能称“事务行为一致”；不能把共同提前消费归入意图通过。

## 有限语义例（完整分母6）

| 例 | IR_spec / RTL_spec / RTL_intent | 可见解释 |
|---|---|---|
| 同offer接受cycle2/4、交付5/8，均合法 | PASS / PASS / PASS | stuttering允许；非逐拍等式 |
| IR合法时序但payload错，RTL正确 | FAIL / PASS / FAIL | RTL在此见证纠正了IR |
| IR正确，RTL合法时序但payload错 | PASS / FAIL / FAIL | 此见证IR到RTL不一致 |
| 两边合法时序、同样错误payload | FAIL / FAIL / PASS | 此见证一致但共同偏离规格 |
| reset前IR已接受offer1，RTL还未接受，分别合法取消 | PASS / PASS / ALIGNMENT_NOT_EVALUABLE | 可比性缺失，不应强判实现错误 |
| 用旧FSM schema表示广播 | UNSUPPORTED_DOMAIN / 有限RTL PASS / NOT_EVALUABLE | 无可信IR轨迹，不能给三路定位 |

见 semantic-examples.json 的明确手工数据。例中IR是“假设已有适配执行器”的抽象事件账，不是现有FSM IR运行。未实现三路分类算法，未验证独立参考；DESIGN_ONLY范围不因6例被放大。

## 研究边界及反馈公平

S三路结果只能陈述可见关系，不能推模型内部认知根因；D无IR不能猜理解阶段。外部保留任务必须真正未参与方法调整，R7受开发影响的源仍属development。未来保持S/D×F/R；F只收双方一致的公开RTL反馈，不额外提供私有意图事实，R以固定父直接RTL无条件重生成，调用机会匹配不等于实际token匹配。新IR域若未来授权需要另行冻结/验证与生产校准，本次0模型/0外部保留任务/0生产接入，无自然错误定位效用估计。
