# 新运行器v2：工程修复与离线验收

仅建立新版本并离线测试，真实模型调用0。不覆盖R3旧runner/judge、计划、资产、证据或成绩；不对旧模型RTL重新仿真，不建立新的真实实验轮次。原任务/参考/资产只读复用。新计划即便准备也必须重新获明确放行，旧R3授权不继承；本轮仅交总控审核。

新角色字段role只由计划赋值first/branch；真实判题全部放入judge命名空间，包含judge.stage。顶层status为judge.status的显式派生，不允许判题字典覆盖id/pair/role/arm。生成结果另放generation。汇总、配对、首次候选统计、实际/策略成本均按role读取。

公共检查与配对共用同一功能状态集合PASS/FUNCTION_FAIL/COMPILE_FAIL/RTL_REJECTED/EXTRACTION_ERROR。非法首次候选的全部原响应保留、两分支均派发（离线以mock供给输出）。格式错误是功能/格式失败，不是基础设施中断；API/未知/仿真基础设施错误仍停止、不重发、不补样。

验收前固定案例：真实Icarus判题stage=simulate与stage=compile；多RTL代码块；ASCII与UTF-8原响应字节长度131071/131072/131073（128KiB门槛按UTF-8字节，等于门槛合法，大于门槛EXTRACTION_ERROR）。校验解析器真实返回和完整campaign→public_feedback→score→summary→seal，不用RTL_REJECTED mock替代格式错误。边界有效夹具是同一手写参考加注释，非法格式不执行编译；保留全部夹具/返回/收据。

仅模型adapter替换为本地确定夹具，真实网络adapter被禁止；公开/隐藏判题使用真实extract_rtl与Icarus。固定一个完整8首次+16分支工程流程及六个直接字节边界，另有API/未知/预算/来源变更与私有隔离回归。人工夹具与mock调用次数不解释为模型样本或研究收益。完整首次非法候选原文保留，超长prompt的真实CLI传输能力不在本次离线验收中验证，不截断原文。

保持24上限/180s单调用/串行/首4服务gate/90分钟dispatch/500MiB、无自动重试和安全封存。离线验收预算10分钟/100MiB。按AGENTS执行test_lab/test_batch/test_dev/test_fsm；生成行为均为离线/mocks，不调用模型。成功后冻结新源码/依赖/工程证据哈希并提交总控；不自动执行模型计划。
