# 新开发判据版本与边界

用户授权范围：独立development材料上建立新握手事务判据，离线验证合法延迟/invalid载荷差异通过、loss/dup/backpressure破坏检出，失败保留，完成交总控；0模型、不扩R7候选、不改R7封存/旧成绩。任务独占handshake-dev-v1及INDEX，本机工具，无学校/远程服务/购买/关机/新聊天。

原始文字CONTRACT.md先于checker/native运行；`fixtures.py`手写source计划和输出时序、人工期望分类，不由checker自动生成golden。`development_broadcast.v`是独立手写one-slot/two-mask实现，参数LATENCY/INVALID_STYLE产生合法差异，MODE1..7人为植入功能故障。`tb.v`固定5项source序列，valid/字段保持至ready；两个消费者独立预声明ready调度、最后16周期都ready1，80条pre-rising-edge trace。计划不从DUT输出或ready提取，collector采样在NBA更新前。source最后未接受也继续valid，故不能空账假通过。

checker与RTLDUT/TB没有共享RTL参考转换器；source与checker/audit同作者，仍可能共享文字误读。复核路径采用flat ledger而非相同queue算法，不声称外部独立作者。22trace完整保留（7合法、11人工功能坏、1输入坏、3轨迹坏），10RTL配置完整保留（3合法、7人工功能坏），不筛除失败/无效分类、不增加外部候选或按成绩选难题。

每次native run源先锁，run已结束后source/evidence精确封存；新调用目录必须不存在，不能覆盖run。默认required回归按AGENTS一次3module、不改代理环境、不隔离重试；未改FSM研究所以没有重跑test_fsm/模型。本轮生产runner/IR/R7原包源均不变，没有执行模型计划SHA。校准包SHA仅审计标识，不能放行模型。

资源预声明24trace/10RTL配置界，实际22/10；native Icarus顺序1、compile15s/sim10s，unit60s/default180s，默认回归内部沿仓库既定最多4workers（不是本校准并发扩容），其新输出位于独立test-results子目录。准备3600s/新包250MiB/软2GiB预算无OS硬隔离。实际native校准不足5s、默认92.391s，无timeout，没有改机器配置或终止其他进程。

具体的reset/公平drain/latency/不评分类别以冻结CONTRACT为准。下一步集成、新外部来源或模型实验需总控另审及明确范围，不能沿用R7负向包或本开发校准SHA直接执行。当前仅提交成果后停止。
