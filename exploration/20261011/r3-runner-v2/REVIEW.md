# 新运行器 v2 工程审核交付

本轮仅修复独立新版本并离线验收，真实模型调用 **0**；未重试403，未重新仿真历史模型RTL。旧版本、证据、研究成绩保持不变。新工程计划已准备但未执行，不能继承旧R3放行。

## 修复结果

- `runner.py` 用计划字段 `role=first/branch` 分组；真实判题字典整体存入 `judge`，其中 `judge.stage` 保留 simulate/compile/extraction。顶层 status 显式派生，判题字段不再覆盖角色、id、pair、arm；配对和共享成本统计统一按 role。
- 公共检查继续条件和配对有效状态共用 PASS/FUNCTION_FAIL/COMPILE_FAIL/RTL_REJECTED/EXTRACTION_ERROR 集合。多代码块或超长首次候选保留完整原响应并进入两臂；API/未知/工具基础设施错误仍停止、不重发。
- 原judge按字节复制到新目录，只读复用原任务和资产；旧runner未改。新runner SHA256：`35f40426fe11dbbc035b31b422f662127706de41cd195269f8629b54b4920ca3`，来源见 derivation.json。

## 离线证据

`runs/acceptance-v1/summary.json`：11组验收通过，25次mock adapter调用（完整流程24次，API停止夹具1次），28次真实编译评估、27次Icarus仿真。模型adapter替换为固定夹具；解析、公共反馈、隐藏评分、汇总与封存使用真实实现。

完整8首次+16分支流程覆盖实际judge字段及多代码块、超长首次候选。首次3个EXTRACTION_ERROR和5个PASS全部保留；24条评分为17 PASS、5 EXTRACTION_ERROR、1 COMPILE_FAIL、1 FUNCTION_FAIL。两臂保留非法候选的完整原文，公开/隐藏隔离与仅反馈差异检查通过。工程夹具配对2 help/2 harm/4 no_change仅用于分类验收，不能作为模型收益。

ASCII和UTF-8分别测试131071、131072、131073原响应字节：低于/等于128KiB通过真实编译仿真，大于门槛返回EXTRACTION_ERROR且不编译。另验证已完成槽不重发、API停止、未知预留不重发、预算/源码变更停止及Windows持锁封存。

父目录 `v2-verification.json` 独立核验：625个新工程证据文件、29个源码/依赖绑定、27条仿真nonce、24条角色与计划绑定及六个边界长度全部通过；6771个历史证据/来源绑定与验收前基线一致，历史成绩未改。

## 回归负结果与局限

按AGENTS执行 `test_lab test_batch test_dev test_fsm`：34个测试，2个Yosys环境跳过；默认环境下两个loopback HTTP测试方法失败，产生3 failures和1 error。Windows配置代理干扰本地mock HTTP；失败后段及汇总保存于父目录 `v2-regression-initial.log`，未删除负结果。

仅对这两个原测试采用进程内、仅loopback地址的 `ProxyHandler({})` 隔离，2/2通过，日志和摘要位于父目录 `v2-loopback-regression/`。原测试、生产代码及全局代理未修改。该条件通过不等于默认环境全回归通过，也不证明生产模型传输可用。

完整超长候选已保留在两分支prompt中，但真实CLI参数/模型上下文对超长prompt的处理未验证；本轮没有生产传输或模型效果结论。未来模型执行需另行放行，审核时应保留这一限制。

## 待总控审核的冻结入口

- 新版本：runner.py、judge.py、PROTOCOL.md、acceptance.py；来源 derivation.json。
- 离线证据：runs/acceptance-v1/summary.json 与 evidence-lock.json；独立核验：父目录 v2-verification.json。
- 未执行计划：runs/prepared-v2/plan.json，24槽全部未启动，计划SHA256 `c5924655c0e1435aa71ab6088cd3bdfec7ed82393f71088e401cc0a1ff06f34e`。

本次提交请求工程审核，不请求扩大旧实验、修改旧成绩或启动模型。
