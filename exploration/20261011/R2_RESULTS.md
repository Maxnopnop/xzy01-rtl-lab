# R2真实执行结果：未观察到反馈帮助

冻结20槽全部启动、全部生成、全部评分，pending=0、基础设施失败=0、重试=0。前4次服务gate通过，之后串行完成。重新生成10/10 PASS；公开执行反馈9/10 PASS、1/10 FUNCTION_FAIL。主分析10对：help=0、harm=1、no_change=9、inconclusive=0。保留这一个反馈较差结果，不扩容、不补样。

| 家族（起始IR来源） | 重复1：重新生成/反馈 | 重复2：重新生成/反馈 | 家族内结果 |
|---|---|---|---|
| rt_sequence（自然保留） | PASS / PASS | PASS / PASS | 2对无差异 |
| sticky_alarm（人工transition故障） | PASS / PASS | PASS / PASS | 2对无差异 |
| event_parity（人工transition故障） | PASS / PASS | PASS / PASS | 2对无差异 |
| request_delay（人工transition故障） | PASS / PASS | PASS / FUNCTION_FAIL | 1对无差异、1对harm |
| debounce3（人工transition故障） | PASS / PASS | PASS / PASS | 2对无差异 |

自然保留IR分层为2对no_change；人工分层8对中7no_change、1harm。这是五家族、同一固定IR各两重复的条件实验，不能视为10个独立家族，不能推断反馈一般有害，也不能估计自然模型错误率。两个分支设计事实、起点、公开例子及期望、实现指令相同，反馈分支额外看到公开例子的执行结果；可见文本不同。此结果不代表端到端生成收益。

唯一失败是request_delay重复2反馈输出：从IDLE接收din=1后立即进入ASSERT_Q，使q提前一拍；规格要求下一拍输出。固定private与独立spec diagnostic都检出3247处不一致，IR agreement也失败（1836处），定位BOTH_DIVERGE。上述RTL行为解释是事后案例检查，不是预声明的新统计分析，不把错误输出修正后重评分。原响应、RTL、首次见证与所有计数保留。

| 观测量（10次/臂） | 重新生成 | 反馈 |
|---|---:|---:|
| input tokens | 106450 | 108332 |
| output tokens | 3609 | 3503 |
| cached input tokens | 44544 | 59392 |
| cache write input tokens | 0 | 0 |
| reasoning output tokens（CLI字段） | 533 | 435 |
| adapter总耗时（秒） | 118.232 | 132.826 |
| generation总耗时（秒） | 113.595 | 128.219 |
| PASS / 1000 output tokens | 2.771 | 2.569 |
| 实际费用 | UNKNOWN | UNKNOWN |

usage字段按CLI原样聚合；reasoning/cached字段不与所属input/output再相加来声称总token。服务只返回requested model，未暴露backend snapshot。没有硬token上限或费用账单；不能称实际token、算力或成本匹配。总adapter耗时251.058秒，真实调用20次、Icarus评估60次；Yosys NOT_RUN。

预声明output-token比<=2描述性子集含9对，均no_change；唯一harm对不在该子集中。这不是总token/算力匹配，不取代含全部10对的主分析，也不据此消除harm或声称反馈安全。缓存量和输入量差异也完整报告。

独立审计核验1073份证据文件、20个原始prompt/request/响应绑定、20份CLI完成事件与usage、工具禁用边界、固定judge资产和60份Icarus compile/sim正常退出及nonce/checks/errors收据，全通过。没有将隐藏检查回喂模型，全部生成结束后才评分。

运行器最后封存时触发Windows已持有run.lock的读取PermissionError，原命令exit1；此时20项生成、20项评分、summary均已完成。单独r2_finalize.py在锁释放后封存证据，没有重跑模型或仿真；保留[收尾修复记录](R2_FINALIZATION_AMENDMENT.md)与[收尾结果](r2-finalization.json)。冻结协议和源码未改。

证据：[原始summary与全20槽](runs/r2-prepared-v1/summary.json)、[独立审计和预声明聚合](r2-analysis.json)、[证据锁](runs/r2-prepared-v1/evidence-lock.json)、[失败RTL](runs/r2-prepared-v1/jobs/request_delay__r2__feedback/dut.sv)、[失败判据](runs/r2-prepared-v1/jobs/request_delay__r2__feedback/judge.json)。此前[准备报告](R2_PREPARATION.md)保留为执行前状态。

R1c的64份历史原PASS无新增错误、失败隔离校准v1、旧4次403和全部旧成绩仍保留。本轮到此停止；没有自动增加家族、重复、模型或检查轮次。
