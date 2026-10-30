# 握手事务判据 v1：独立开发离线校准

本轮建立独立`checker.py`，以预先固定source计划、实际valid&&ready输入接受记录、逐consumer输出事务FIFO与阻塞保持为判据；不借用参考全端口逐拍波形。**0模型、0候选扩展、0旧RTL重评分**。R7原包与旧分数保持。本版本没有接入R6/生产runner、修改IR或提示模板，也没有模型执行计划。

|校准分母|PASS|人工功能故障检出|环境/轨迹不可评分|预声明结果匹配|
|---|---:|---:|---:|---:|
|22手推trace见证|7|11|1 INPUT_PROTOCOL_FAIL + 3 TRACE_INVALID|22/22|
|10手写RTL参数配置（真实Icarus）|3|7|0|10/10|

合法变体覆盖0拍组合传播、同拍新输入与旧输出、独立消费者消费、延迟5拍手推/3拍RTL、valid0时data/last改变或X/Z；事务序列相同即可通过，不要求ready/latency/invalid字段逐拍相同。带明确取消规则的reset见证通过，取消量另记aborted。7合法trace与3合法RTL并非10独立外部设计。

故障包含末事务丢失、额外重复、次序交换、有效data/last损坏、stall后data/last变化或valid撤销、输入永不ready及超固定观察窗口不交付。输入环境违约、unknown有效控制、没有公平drain尾部或缺cycle明确不评分，未误报PASS。source计划独立固定，不能因DUT拒收全部输入而形成空账PASS。

真实RTL主要失败见证：loss消费端0最后一项`[254,1]`在source cycle16接受，cycle79仍缺失；duplicate消费端0在cycle11多收`[17,0]`；stall_data在cycle5期望`[17,0]`却观察`[16,0]`，BACKPRESSURE_FAIL；never_input_ready到cycle79尚有5项未接受，LIVENESS_FAIL。每配置的首次至多8项差异、完整counts/accepted/delivered与raw trace原样保存，FUNCTION_FAIL是人工故障的成功检出，不能当模型失败或自然错误定位收益。

`calibration-v1/`保存22原输入与判定、10原DUT配置的argv/执行文件hash/退出状态/stdout/stderr、raw trace/规范化trace/判定、source-lock与精确evidence-lock。10compile/10sim全部exit0；fault仿真exit0只说明正常采集轨迹，功能判定仍FUNCTION_FAIL。原DUT/TB是本任务手写，同作者，不是外部独立作者golden。独立交叉核验使用`audit.py`的逐epoch平面输入/输出账及相邻stall比较，不import生产checker或生成参考RTL期望。

`unit-v1/`一次3个unittest通过（复用上述22见证及关系测试，不另加独立样本分母）。仓库required默认`python -m unittest -v test_lab test_batch test_dev`只运行一次：**24 tests，failures3/errors1/skipped2，exit1**，92.391s。原默认环境与代理设置未改；local mock HTTP `RemoteDisconnected`，ok error、truncated/observed数量/call-cap失败保留，缺native Yosys2skip保留。未隔离transport重试，也不据此宣布已确认代理根因。原stdout/stderr及receipt在`default-regression-v1/`，不混校准指标、不称仓库全PASS。该回归的API路径是本机synthetic mock或unconfigured guard，非实验模型调用。

限制：固定2consumer/8bit+last/single clk；80周期窗口、至少8周期公平ready尾部，仅有界轨迹，不允许任意无限延迟、不证明无界活性或完整AXI规范。有限缺失一般不能区分永久丢失与超窗口延迟，人工MODE源码的丢失机制另有证据。采样前沿之间的glitch/时钟间稳定/异步reset/CDC未验证；native只初始同步reset，中途reset仅手推事务语义见证。没有推广到COBS/tap/truncate/第二时钟，没有解除R7计帧参考歧义，也没有验证新IR域可表达事务关系。

所有因R7问题而影响此方法开发的接触材料未来只能作development，不能再冒称同方法的未调优heldout；本轮未读取/适配R7 DUT/官方test以作新golden或重算R7成绩。协议/覆盖和来源分离说明见CONTRACT.md/PROTOCOL.md/COVERAGE.md；冻结后停止，交总控独立审核，未自动启动后续。
