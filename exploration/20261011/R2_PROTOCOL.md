# R2：反馈与重新生成，有限预声明

本轮只准备、冻结和离线验收；真实20次调用等待总控后续放行。本方案不恢复或重写原factorial20-v1的4次403。

选择五个开发家族，各两次重复、两臂，共20槽。rt_sequence使用paired-v1的real_overlap自然保留IR，其余四家族使用各自transition人工故障。按固定manifest选择，不按模型表现择样。一个自然家族与四个人工家族分别报告，不合并成自然错误率。

两个分支共用完整规格、设计事实、v2公开例子及期望、同一个初始IR、同一个实现指令、gpt-5.6-sol、low reasoning、180秒限制、一次生成机会。regeneration分支不带执行结果，feedback分支仅多出这些已公开例子的检查结果。共同指令允许修正候选并生成RTL；因此估计的是提供计算反馈的条件效果，不是额外修复轮次的收益。每个pair保存共同文本、初始IR和完整prompt的精确UTF-8字节及哈希。

生成禁止工具和隐藏数据访问。反馈只调用bank.feedback(candidate, public_contract)，离线用mock禁止oracle与product_check以核验边界。固定private testbench、spec diagnostic、IR/RTL agreement在全部本批生成结束或基础设施停止后才运行；不会把结果回喂模型。Yosys独立标NOT_RUN，不混入Icarus分数。

上限20次新调用，串行（<=2并发），先4次服务可靠性门槛，仅看生成是否成功，不看功能分数。任何API_ERROR、工具使用、超时、未知中断停止整个campaign；不重试、不换模型、不补样、不退还已预留槽。保存失败及pending完整分母。执行必须显式传冻结plan SHA；当前准备命令不含执行授权。

CLI无max_output_tokens硬上限；不能称实际token或费用相等。完整保留输入/输出/缓存token、耗时、原始响应和CLI事件。预声明分析：10对help/harm/no_change/inconclusive；五家族为簇，报告簇内两重复。自然/人工分层。token敏感性仅在已完整对内标记两臂output token比<=2的子集，仍保留全20槽主分析；不补样、不删主结果。附每臂PASS/1000 output-token效率，缺失usage标UNKNOWN；实际费用没有账单时UNKNOWN。小样本不做泛化或显著性收益主张。

离线验收使用五个正确独立参考RTL（每个三种判据，共15次Icarus），并用mock验证API失败停止、未知中断不重发、4调用gate与20上限。mock不算真实模型结果。全部source/hash/固定judge资产先锁定；任何变化拒绝执行并新建协议。预算：离线10分钟、200MB；真实campaign最多60分钟、500MB；compile15s/sim10s，单个模拟器，无购买、充值、模型训练。
