# R5离线准备交付：待总控审核，不执行模型

已完成参考共源/覆盖审计、三个新开发机制、S显式IR vs D直接RTL的匹配流程与F/R强基线、真实Icarus校准、48槽离线控制流和新冻结计划。**0真实模型、48槽全部未启动**；不执行v2/v3/R4旧prepared，不重判历史模型RTL或修改旧成绩，没有重试403。

新计划SHA256：`752be8b79f544a86f0961ab50e5a8645ea7d18132792670d9373e095fd295b4e`，在runs/prepared-v1/plan.json与plan-lock.json。此为准备边界，不继承R4放行。总控须审查本新计划/原始校准/锁后明确放行新SHA，本turn停止，不自动执行。

## 研究设计与公平性

3机制×2重复，每例四共享+四分支，48唯一。S：真实模型JSON意图→首次RTL→最终F/R；D：直接RTL→提供D1的无条件重新生成→最终F/R。D2固定为分支父候选，即使D1通过/D2失败也不选优；保留全部D1/D2输出。四策略各6分母/18阶段机会，半共享分摊各12，不能把72完整共享机会写作实际调用。

事实/接口/公开事件/模型设置匹配。D无teacher IR/参考RTL/schema；S有显式可执行schema为处理因素。最终两流程均只用父RTL和规格，F仅增加相同规格层RTL公开执行结果，不提供S专属IR诊断；R保留强完整重新生成指令。三路S诊断仅生成停止后隐藏评分，D没有中间意图不能虚构理解/实现定位。无显式IR不等于无内部思考。两早期RTL尝试与IR+RTL是流程处理差异，不能解释成纯格式变量。

串行gpt-5.6-sol/low、48唯一上限、180s/调用、10800s派发、750MiB阈值、256KiB prompt/16KiB IR/128KiB RTL/沿用2MiB进程输出限制；首次四返回服务gate只看基础设施，不筛格式/功能。基础设施或未知停止，无重发/补样/换模型/扩轮。全部格式/unsupported/功能/基础设施/INPUT_LIMIT/PENDING保留固定分母。机会匹配不等token；主/敏感性及费用UNKNOWN预声明于PROTOCOL。负结果/天花板保留，完成即停。

## 新机制及参考范围

- phase_snapshot：分离fall采样与rise发布，两个边沿寄存器bank、暴露sample；不是旧posedge DFF改宽度。
- escape_frame：转义控制token变payload、跨gap保存escaped、重启/提交/flush；不是旧固定bit序列识别。
- masked_ring_alloc：多资源同时占用、任意释放及稀疏洞搜索/满时同拍重分配；与旧轮转单owner共享轮转概念，不能称完全无语义交集，但核心状态与优先级不是简单扩宽。

参考由过程Python、独立手写SV及不同推导的payload列表/集合距离参考交叉检查；没有IR转换生成两条核心参考。**同作者/同文字风险依然存在，未有外部独立作者审核**。人工正确IR及确定性AST→SV仅校准。REFERENCE_AUDIT披露旧判据共享转换/共同oracle、R4内部不可观察规则与公开盲点；COVERAGE逐规则对应手推状态/事件及缺口。新私有补高/低clk中途reset与稳定level释放、逐输入bit保持，仍binary/#2采样/固定参数/有界，非完整state×input、X/Z/瞬态/无界/最终集/PPA证明。

公开/隐藏事件数：phase30/9128，escape123/6855，allocator58/6678。期望由冻结过程oracle产生；两路径一致不排除共同误读。assets/lock.json和coverage.json、参考/源码/提示词/协议先冻结。

## 原始校准与控制流

成功runs/calibration-v3：3手写参考公开/隐藏PASS、3核心目标突变公开/隐藏FUNCTION_FAIL、3人工正确契约确定性转换隐藏PASS、1真实COMPILE_FAIL；18手推状态与六组过程/不同推导/人工IR交叉检查一致；5格式/域错误分类保留。该成功run16编译/15仿真。没有大规模突变枚举，不能作为自然模型收益。

runs/control-v1：48离线生成callbacks及1额外故意API失败callback，真实固定judge；12组控制检查。包含真实stage字段与role隔离、S坏IR和多RTL块仍保留双臂、D1 PASS/D2 COMPILE_FAIL却固定使用D2、S/D同规格层反馈、隐藏在生成完成后、48/72/半共享费用账、固定6分母、未知预约1/47pending、API失败不重发、256KiB超限不预约、ASCII/UTF8 128KiB上下边界。人工2help/2harm/8no_change仅校准，不是模型实验；实际模型收益当前不存在。

保留负结果：precheck-v1人工allocator表达式7656字符超限；calibration-v1简化后仍超过512 AST节点；calibration-v2误用Verilog保留字release端口被原policy拒绝。分别保存原源码snapshot、失败说明及原始日志，另新校准版本修正teacher表达式、rename新端口free_req，不放宽根策略或IR域。两个失败run在phase/escape上的已做编译/仿真保留，未覆盖。累计本轮103编译、100仿真（含两失败run和离线控制）；不包含旧模型RTL复测。

required默认环境回归只执行一次：34测试、3failures/1error/2Yosys skips，runs/regression-v1完整日志封存。不隔离代理、不循环重试，不称全回归通过。v3运输只读复用已审核代码；服务最大context、后代进程树清理仍未独立完整验证。原公开盲点及旧天花板保持。

## 核验及审核入口

verification.json：33新源码/资产绑定，110校准源绑定（失败版按snapshot），全部新seal集合/哈希、103编译和100sim的原命令nonce/receipt/checks核对通过；8066旧绑定及4860 R4封存文件/源锁不变。audit-receipts.json含原日志相对路径与nonce/error计数。复核不调用模型或仿真，未重写旧材料。

审核依次读PROTOCOL、REFERENCE_AUDIT/COVERAGE、tasks/reference_alt/三SV、prompts/intent/runner、calibration-v3 anchors/results原日志、control-v1 fixture-plan/full/results及负分支、regression、prepared-v1 plan/locks、verification与packet-lock。LITERATURE只读一手摘要，结构IR/仿真反馈已有先例，增量仅待验证的公平流程消融，不声称首创/跨论文提升。当前只提交准备，等待精确新SHA审核。
