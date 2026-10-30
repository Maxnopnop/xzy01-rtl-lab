# R6 发现与边界

- R5第21预约后约2秒local app-server stop_process，之后新桌面实例启动；触发原因仍未知。旧适配器返回后才保存stdout/stderr，无法证明服务端结果。新适配器只改善可观测性，不保证宿主死亡时完整记录或根因修复。
- R3/R4全PASS及R5返回皆PASS没有自然研究增益或阶段偏差；增加机制不保证难度。新任务开发前冻结规则与参考，不先试模型挑题。
- 现有参考同作者；不同推导/实现不等于外部独立作者。人工故障校准不计自然模型收益。
- 默认代理回归已知失败保留；本轮一次required回归，不隔离重试。

- 新恢复必须跨调用内部一致性，额外校验plan/job/model/父样本/精确prompt；v1原计划保留，engineering-v2追加4人工槽位边界通过。完整exit前已出现completed仍UNKNOWN；完整exit后缺summary可离线重建，但不重发。
- 新队列/除法/join的A过程、B年龄字典/divmod延迟/可选槽抽象、C手写SV与手算一致；同作者共享文字和打包，不称外部独立。仅9针对性Icarus校准，不声称所有时序覆盖。
- 实际default required仍3failure/1error/2skip；准备门控字段KeyError修复前原源码/失败封存。无模型、生产CLI预检或403重试。v2最终源/资产/预算已冻结，审核前不执行。
