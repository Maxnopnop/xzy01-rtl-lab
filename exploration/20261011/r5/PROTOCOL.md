# R5 冻结协议

仅新开发pilot准备，0模型；新SHA经总控明确放行才可run。3机制×2重复×8唯一槽=48，串行gpt-5.6-sol/low，180秒/调用，10800秒派发窗口、750MiB派发前阈值、256KiB prompt、16KiB意图、128KiB RTL、沿用适配器2MiB输出限制。前4真实预约返回无基础设施错误服务gate；格式/功能错误不是gate淘汰条件。基础设施/未知停止，无重发/补样/换模型/扩轮。阈值不是服务端token硬限。

S：JSON可执行意图→首次RTL→F/R最终RTL。D：直接RTL→无条件再次生成RTL（提供D1原文）→F/R最终RTL。D2永远为分支父候选，不按成绩选D1/D2；保存两者及所有槽。无IR指不请求/不提供显式外部IR，不否认模型内部推理。该对照是两种匹配调用机会流程，S中间意图与D额外RTL尝试本身为处理差异，不是纯表示格式因果效应。

每例四共享槽S1/S2/D1/D2+四分支，共享24唯一、分支24唯一。四策略各6分母/18机会，半共享各12分摊（合48）；完整共享策略账不可相加当72实际。真实input/output/cache/reasoning/耗时报告；未知保留None，reasoning为output子集不加重复费用。费用UNKNOWN。全部firsts/IR无效/unsupported/多块/超限/基础设施/PENDING均保留固定分母，不按长度筛选。

两表示提供同一文字规格、接口、公开输入/期望及模型设置；D无schema/teacher IR/参考RTL。S schema是有意处理信息。最终F/R相同事实/父RTL/修订指令，F只增加该父RTL同规格层公开执行结果，S不增加IR_spec或RTL_intent诊断。D2也无反馈，候选不评分选优。全部生成停止后才隐藏评分和S三路诊断；D仅RTL_spec，无法定位理解/实现分歧。人工正确IR和确定性转换只校准不作模型成绩。

IR为JSON对象timing(reset)、registers(width/reset)、next_rising、next_falling、outputs。两next的键必须不相交且合并为全部寄存器，每寄存器唯一边沿；1..16寄存器1..8bit、65535常量、4096字符/512节点每表达式。支持+-、&|^、常量0..7位移、单比较、and/or/not、条件表达式；无函数/数组/任意Python。同步reset仅本边沿寄存器bank；async低复位全bank；none仅初值。并行old-state更新、赋值宽度截断；binary事件不处理X/Z。D可自由写RTL，不限同一IR实现域；unsupported单列并纳全分母，支持域敏感性仅描述。

新题非旧题参数扩展：双边沿snapshot有两个独立更新域；escape是变长转义控制token变payload及gap/restart/commit；allocator支持多同时占用与任意释放/稀疏holes，不是单owner仲裁/FIFO，虽共享轮转概念，不称完全语义无交集。固定参数、同作者、开发拟合、有限#2事件，没有无界/模拟瞬态/最终集/PPA证据。

分析预声明：四策略全分母PASS，按机制及重复列原status；同流程F-R help/harm/nochange/inconclusive、同臂S-D配对差值。另列D1/D2及SIR/首次；不能按失败挑样。主分析机会匹配；成本敏感性用所有例实际token/cached及每PASS成本（零PASS定义未知），描述支持域内子集及固定任务分层，不删原主分母，不做事后token阈值优势检验。若全PASS，天花板负结果如实报告，停止。

默认代理required失败保留，无隔离重试或403重试。v3生产运输只沿用已审核代码；服务上下文及后代进程树终止仍未经独立完整验收。本轮不重开旧工程。
