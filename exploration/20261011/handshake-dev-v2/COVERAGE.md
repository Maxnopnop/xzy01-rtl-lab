# 覆盖与分母

| 材料 | 分母 | 观测 | 限制 |
|---|---:|---|---|
| 新手推边界 | 8 | 4PASS/4FUNCTION_FAIL，8完整期望匹配 | 同作者、不是8自然模型样本 |
| 新native配置 | 8 | 5PASS/3FUNCTION_FAIL，8状态/7类别条件匹配 | 人工fault参数、同一个新TB |
| 实际工具 | 8compile+8sim | 退出0、stderr空、640pre-edge事件 | 进程成功与判题功能失败分开 |
| 中途同步reset | 4native | 2合法flush/2残留故障 | 初始reset+8/9中途；非异步 |
| 另一缓冲 | 3native | queue reset正负及8beat连续 | 深度2独立队列，不证明全部状态 |
| 输出因果 | 3native | 同拍PASS/提前validPASS/提前consumeFAIL | 单笔固定ready场景 |
| 意图设计语义 | 6 | 文档手工例、未执行IR/分类器 | DESIGN_ONLY_NOT_VERIFIED |
| 旧默认回归 | 原24 | 原3fail/1error/2skip exit1保持 | 非本轮新执行 |
| 本轮模型/外部候选 | 0/0 | 未执行 | 无自然模型收益结论 |

原v1的22/10没有重跑、不并入v2独立分母。两批不能合并为独立样本统计。native3FUNCTION_FAIL仅代表本有限人工破坏在真实仿真中检出。shared_reset_stale错误类别不符为真实保留的校准负结果，整体exit1。新校准只执行一次，无额外单元测试分母。
