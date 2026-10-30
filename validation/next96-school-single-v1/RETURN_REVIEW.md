# 第25槽学校DC回传核验

2026-10-24：next96-dc-slot025-v2，Prob094_gatesv / gpt-5.6-luna / no_rag / sample1。用户在ecelvd702.ece.local手工运行单例。已收到return-synth-20261024T061542Z-8bbc5980.zip，SHA256 c866fcf7e35ab27843be669bd4360c894eca46826802d0760fc84757c559d9c6。

## 结论

有证据确认DC X-2025.06-SP2完成该样本的标准单元映射和网表/DDC导出。执行退出码0，完成nonce、payload-lock、原RTL与原结果哈希一致；Nangate typical .db实际可读且指纹3c205f46310315953d992fb014e814a1f12e9cb2a0030f900dc366131f7fc425，1851392字节。此次只读核验0模型/EDA调用。

不是全日志无错误：附加report_lib出现3条LCSH-3错误，要求检查Library Compiler安装。该报告命令未阻止后续映射，主流程输出和完成标记齐全；仍保留原错误，不修改脚本、不重跑。库单位尚未由本次report_lib确认，不得推定面积为平方微米或时延为纳秒。

## 观察值

- area.rpt：Number of cells 15；combinational 14；sequential 0；black boxes 0；buf/inv 4；Total cell area 13.300000（库面积单位）。Total area undefined，wire load net area为0，不能视为布局布线后总面积。
- timing.rpt：typical、wire load 5K_hvratio_1_1；显示的最坏路径arrival 0.07，临时max_delay 10.00，slack MET 9.93（均按报告时间单位；待核库time_unit）。原任务无性能指标，本例未设输入slew及输出负载，不能视为实际外部条件下时序签核。
- constraints.rpt：This design has no violated constraints，仅针对已设置约束。
- check_design：LINT-29 in[0]直通out_any[0]；LINT-52 out_both[3]常0。这两个输出位是原题明示don't-care，告警不构成该题功能失败。VO-4提示导出assign/tran，网表实际含对应assign连接；保留原输出。
- 网表实际包含XOR2_X1、NAND2_X1、NOR2_X1、INV_X1标准单元。商业综合网表还没有用学校单元仿真模型做功能仿真；此前94/96网表仿真是本机Yosys网表结果，不能替代本次DC网表验证。

## 下一步

只读核查同工艺库Liberty的单位与学校可用Verilog仿真模型。模型字节留在学校，用同一个原题testbench/reference做单例DC网表功能仿真，另存结果。不要重跑综合，不扩展学校批量任务。学校共享目录刷新曾延迟，原始回传已本机保存，无需重复发送。

原始报告在returned-20261024T061542Z；机器核验记录return-audit.json。COMPLETED_REVIEW_REQUIRED是运输/完整性检查结果，上述人工审核给出具体结论与未决项。
