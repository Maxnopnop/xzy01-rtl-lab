# 预声明覆盖（尚未执行）

完整cases.json固定12配对描述，11计划执行、1spec含糊不执行。阶段B IR11/compile11/sim11为本计划精确机会，不是用满总授权12/24/24。每轨迹80周期，IR低/高共160事件；native PRE/POST共160条，握手评估只用80 PRE行。顺序并发1，不自动加例。

| 场景 | 覆盖 | 预期IR / RTL / 意图 |
|---|---|---|
| 01 | 完整当前IR one-slot映射+160逐相位身份比较 | PASS/PASS/PASS |
| 02 | 合法延迟/stuttering | PASS/PASS/PASS |
| 03 | 每consumer深度2独立队列不同合法结构 | PASS/PASS/PASS |
| 04 | 提前valid未消费、后同拍接受 | PASS/PASS/PASS |
| 05 | 同拍接受交付 | PASS/PASS/PASS |
| 06 | 最终序列相同但提前消费 | PASS/FUNCTION_FAIL/FUNCTION_FAIL |
| 07 | 已部分交付后同步reset取消、160逐相位比较 | PASS/PASS/PASS |
| 08 | 跨epoch残留 | PASS/FUNCTION_FAIL/FUNCTION_FAIL |
| 09 | 固定reset导致接受/取消集合不一致 | PASS/PASS/NOT_EVALUABLE |
| 10 | reset语义缺失、不执行 | SPEC_AMBIGUOUS/SPEC_AMBIGUOUS/NOT_EVALUABLE |
| 11 | source稳定性破坏、环境无效 | INPUT_PROTOCOL_FAIL/INPUT_PROTOCOL_FAIL/NOT_EVALUABLE |
| 12 | raw保全、评估view缺样 | PASS/TRACE_INVALID/NOT_EVALUABLE |

意图不可评估预期4/12，功能关系FAIL预期2/12；不能合成“10/12功能通过”或准确率。原v2 8+8不并入独立样本、15/16完整条件/exit1不消除；旧默认24回归exit1继续保留。本批都是人工开发夹具，0自然模型收益分母，0外部候选。
