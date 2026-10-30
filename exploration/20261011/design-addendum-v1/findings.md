# 补正发现

R6不是1bit Moore：最多16个每个1..8bit寄存器，条件/算术等表达式，三种低有效reset域。next边沿bank用旧env并行评价，outputs使用更新后state；judge事件驱动后#2比全输出，与v2pre-edge握手账相位不同。现TASKS仅三题没有广播。潜在one-slot及14寄存器两消费者双槽预算不能代替完整映射验证。reset对齐、offer_id/driver及私有反馈公平性仍是设计约束，DESIGN_ONLY保持。
