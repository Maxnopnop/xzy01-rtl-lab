# R7 外部候选准备：负向来源关卡已冻结

12候选完整分母，纳入0，排除12；没有生成执行计划或模型prompt、没有48个预约槽。准备边界48不等于已计划48。**0模型、0预约、0自然候选成绩**，2原参考compile/2sim只作判据/参考观测。交总控审核后停止，不自动换源、扩候选或用同作者原创补数。

固定两个上游commit，所有原字节/许可/作者与URL见SOURCE_MANIFEST.json，完整候选及每项理由见candidates.json。轴流来源已停止维护，按历史版本核查。cells四旧路径404保留，README明确映射三cc名称；fifo_v3身份未核实，不以cc_fifo替代。旧source-download-lock.json是空占位，不作为来源哈希证据；本交付以SOURCE_MANIFEST.json/packet-lock.json为准。

主要缺口：五候选原文字与测试只有流/帧契约，不固定R6逐事件全输出的payload/ready/latency；三候选域不匹配（COBS编码原256FIFO，两个独立CDC时钟）；两候选保守判为旧deglitch/round-robin家族；一个原ID路径身份未核实；计数器存在README计帧与单拍观测的待解歧义。不是已证明作者RTL整体错误，也不是证明没有任何可能适配方法。

广播原源码valid=0时数据5a5a，mid-reset只清valid/ready且保留a7a7。功能等价地屏蔽invalid载荷会在精确全输出比较中不同；没有改R6判据掩码。计数器8bit参数下接收单拍last，输出tag42/tick02/byte01/frame00；保留原输出，未修baseline。原测试只阅读未执行，其独立完整性未通过；不称官方全测试PASS。

冻结四臂方法/IR/分类及预算的承继规则在PROTOCOL.md；执行case为空，execution_plan_sha256=null。packet SHA只标识本负向准备包，不可作模型执行放行。源、计划与成绩R1–R6不动；默认required回归负结果仍保留。本轮无实验运行器改动，不重开运输工程/默认回归或模型服务403请求。

只读核验：从outputs/rtl-batch执行`python exploration/20261011/r7/audit_packet.py`。只读取原源/封存/调用访问记录和本包，不运行参考/模型，不写旧文件。核对prior-lock全部19971原绑定，方法锁、来源哈希、候选12分母、原始compile/sim日志与收尾包哈希。报告中的0纳入是来源关卡负结果，不能得出IR或反馈一般有效/无效。
