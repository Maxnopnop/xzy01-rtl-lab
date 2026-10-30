# R6 离线准备交付（停止待总控审核）

当前可审核执行候选是 **engineering-v2/runner.py** 与 **runs/prepared-v2**，计划 SHA256：

`f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4`

本次真实模型调用 **0**，48槽全部未启动。准备边界不是执行放行；未收到总控精确SHA指令不得运行。R5继续封存，不重发第21或补27，旧成绩/负结果/学校任务不动。

## 交付与实际验收

- 新流式记录和保守恢复：原bytes/时间/chunk hash/nonce、请求/模型/本地PID身份、退出凭据；关键文件原子写及fsync。人工OS校准v1/v2/v3各13检查，当前v3带源snapshot；6组事件/最终文件/批重建边界检查及新增4组计划槽位/父样本/prompt/model绑定通过。写者停止不等于子进程停止，活进程拒收尾；completed但缺exit proof仍UNKNOWN。只有可证明原完整返回才离线重建到新输出、不修改原证据。无全局kill，后代树清理UNVERIFIED。
- 新机制：ordered_retire、restoring_divide、tagged_join，各两重复；规格/3SV参考/6公开隐藏资产/有限IR域/模板/顺序和seed冻结。Python过程、另一抽象推导、SV、22个手算rising值一致，6正确参考判题PASS，3目标负例FUNCTION_FAIL；专属9compile/9sim、32695事件检查。另有required回归自身EDA子过程，不混作研究统计；本包未聚合其EDA总数。
- 四臂协议仍为S显式模型IR→首次RTL→F/R，对照D直接RTL→无条件D2→F/R；同设计事实/公开RTL_spec反馈，D2不择优，S私有IR诊断只后评分。两版人工48槽流程及输入/提取边界验证角色与judge.stage隔离、EXTRACTION_ERROR继续两分支、完整分母和费用分摊；人工不算自然收益。
- 默认必需回归只跑一次：34测试、3failure/1error/2skip，完整失败stdout/stderr/receipt封存；未改代理或隔离重试。离线准备另有GBK读取UTF-8错误，以及首次prepare从控制summary读取不存在status的KeyError；后者在任何计划写入前失败，源码snapshot和failure.json封存。修正gate读取control-audit后准备成功。
- 只读审计通过41源绑定、16445旧文件绑定、1398已封存run绑定（含嵌套重复绑定），9个nonce/命令/原判题凭据及原vector位域逐行对齐；原v1计划与源仍有效，新的v2额外绑定恢复脚本。准备磁盘约8MiB快照、无遗留本测试子进程。

详细入口：[PROTOCOL](PROTOCOL.md)、[ENGINEERING](ENGINEERING.md)、[REFERENCE_AUDIT](REFERENCE_AUDIT.md)、[COVERAGE](COVERAGE.md)、[verification.json](verification.json)、[verification-vector-bindings.json](verification-vector-bindings.json)。重新核验仅运行 `engineering-v2/verify.py`，不运行模型或仿真。本轮首次prepare失败见 `runs/prepare-failure-v1`；默认回归失败见 `runs/required-default-v1`；人工与真实Icarus证据各有独立seal。

## 版本与冻结

根runner.py及prepared-v1（SHA `74c4da7614531ba3394d2c80174c95e84feb27fab4d05fc5da47115e73bde7d4`）保留，不作为放行候选。首次离线恢复已核调用内部完整性；冻结检查发现还需计划/槽位/父阶段/prompt绑定，故新增engineering-v2，仅扩展新源和新prepared-v2，不覆盖v1。新恢复脚本以原批锁、原plan SHA及source hashes、预声明父样本、exact prompt与请求model/limits共同核对；输入替换、模型替换、父样本缺失均UNKNOWN。CLI不自动续派中断批次。

公开首阶段prompt在plan/prompts保存；后续全文依赖真实父返回，当前冻结模板及拼接规则，未来逐次保存精确原文/SHA。fixed开发刺激seed为61011+任务索引，顺序按任务索引/重复号确定，provider seed未发送。后评分四策略每臂6分母/18机会/半共享12；最多48唯一串行预约、gpt-5.6-sol/low、180s单次/10800s派发、256KiB输入/2MiB软日志上限、750MiB磁盘阈值；服务异常/403/未知停止，无重试/换模型/补样。

## 限制与审核请求

新机制的区分力是待检验假设，不能从人工检出宣称模型准确率或自然阶段定位收益。全部为经过设计/校准的原创development；本轮候选保留集为空，不是独立最终集。同作者参考有共同误读风险，有限binary/#2/固定参数短轨迹，无全状态穷尽/无界证明/PPA/生产恢复保证；矩阵明确记载已知缺口。当前没有真实费用或模型账单，费用UNKNOWN；人工usage不计账，未来缓存/reasoning不重加，未知调用不填0。

请总控独立审核恢复边界、原失败保全、参考依赖/覆盖、四臂公平性/支持域、冻结SHA及完整分母。审核意见另存新文件。通过后才按已有授权发一次精确新SHA有限执行；未放行前保持0模型，准备完成即停，不自动开轮或扩大测试。
