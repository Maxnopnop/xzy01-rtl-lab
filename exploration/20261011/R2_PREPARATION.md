# R2准备结果（未调用模型）

已冻结[协议](R2_PROTOCOL.md)、[运行器](r2.py)、[20槽计划](runs/r2-prepared-v1/plan.json)、[计划锁](runs/r2-prepared-v1/plan-lock.json)和每槽UTF-8完整prompt/common/candidate文件。五开发家族×两重复×两臂；1个自然保留IR家族、4个人工transition故障家族。当前真实调用0，20槽均未启动；不重试旧四次403。

[离线验收](runs/r2-offline-v1/summary.json)通过：10对共用规格/初始IR/公开例子与期望；反馈只多出公开例子执行结果；禁用oracle和product_check仍能准备全部prompt。五份独立正确RTL在固定private与spec diagnostic均PASS，对错误IR的agreement均FUNCTION_FAIL（15次Icarus）；这只证明判据与边界工作，不计模型收益。

26次mock adapter调用验证20上限、成功完成不重发、首个API错误停止且不重试、未知中断停止、四次服务gate、第五次错误后停止。mock失败不是真实403请求。真实运行串行，source/资产变动或plan SHA不符拒绝运行；失败保留分母、原响应、usage、耗时、CLI原日志，无补样。

服务恢复来自总控另行执行的proxy smoke（validation/model-route-20261011/proxy-smoke-sol/result.json），不是本探索新调用；这里只锁定新codex_network_adapter.py，不改旧adapter/runner。执行命令需总控后续放行及exact plan SHA，本轮未运行run子命令。真实生成完或服务停止后再评分；Yosys另列NOT_RUN。

预算是同模型/推理设置/调用机会相同，CLI没有硬token上限，因此不能说等实际token/费用。所有主结果保留；预声明output-token比<=2敏感性、按五家族聚合help/harm/no_change/inconclusive、自然/人工分层、成本效率；未知usage/费用显式UNKNOWN。单调用180s限制；协议60分钟是campaign资源预算，当前运行器串行按20槽和每调用限制有限，不具备独立60分钟硬杀进程机制。

本轮R1c合计80次Icarus，加R2离线15次，共95次；真实模型调用0。没有效应估计、没有新成绩。
