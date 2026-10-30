# R7 发现

R6已验收：48clean/6IR42RTL有限PASS，四臂6/6、12反馈same、18三路ALL_MATCH；无自然收益/阶段定位样本。新准备必须改参考/来源测量依据，不据全PASS追难题或自动扩批。外部来源独立作者≠训练未见，项目未调优≠独立最终集。

已按原12候选清单固定axis commit48ff7a7e2ef782cf778d47910cf85835c64b1bce（2025-02-27）、cells e73baaec2ca665cd80c3c384e9258e35242b829c（2026-09-18）。axis原作者README明确deprecated；源读取219637 bytes，8axis模块成功，4cells初始路径404保留，未重试403。paired-v1已有debounce3，serial_deglitch若存在须按近重复排除。

重要判据风险：AXI流功能契约未必固定所有ready/invalid-data/微架构周期；R6逐事件全端口精确检查是否适用需审阅原规则和原测试，不能把任意合法流水线差别制造成自然错误。未作方法/域/提示修改，尚未选定或校准候选。

R7接回：R5重复交付沿用原验收，本次R5只读复核0写入。cells README实指cc_serial_deglitch/cc_edge_propagator_ack/cc_rr_arb_tree，已保存三原文件；cc_fifo只作为fifo_v3缺路径的相关背景，不断言身份。原AXI测试broadcast/COBS/length-adjust均按recv帧数据断言，未建立全输出逐拍golden；broadcast源valid=0时可装载输入payload，原功能测试不检查此payload。cobs_encode内置两个DEPTH256 FIFO，原实现超16×8状态域；CDC两来源双独立时钟，不可映射成R6单clk双边沿而不变契约。无方法修改/模型试跑。

最终negative decision：5全周期契约不够明确、3固定IR域不匹配、2保守近重复、1原ID未核实、1参考计帧规则歧义，共12。单拍stat原byte1/frame0输出未修；广播invalid-data和reset保留payload说明精确全输出判据不能无审计移植为帧功能golden。没有自然错误定位收益可估，未把source观察算模型分数。若后续改握手/方法需新开发验证，这些影响改动的接触候选不能仍称未调优heldout。
