# 阶段A冻结与阶段B一次执行边界

当前仅阶段A。允许读取源/证据、写新样例、JSON和Python AST静态校验/哈希，读取工具文件元数据；禁止import目标解释器、调用其parse/run/evaluate、仿真/编译/校准、模型、默认回归或旧实验重判。新harness尚未执行，语法静态核验不等价功能通过；Verilog无编译校验。保留全部不足，不为取得PASS提前运行。

阶段A冻结prior-lock（旧字节）、tools（exe SHA/Windows元数据，若无可读版本就UNKNOWN，未运行version命令）、新源、cases、完整IR、手算和本协议到plan.json。plan-lock记录精确plan SHA。总控审查须明确接受流式插桩、task overlay、PRE/POST适配、reset取消和NOT_EVALUABLE规则，再绑定该SHA一次放行。无生产runner/FSM修改，不执行AGENTS的生产runner默认回归；若后续要求改生产runner，先报告而不执行。

阶段B命令只在新精确SHA放行之后由总控要求执行：

```powershell
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' exploration/20261015/transaction-alignment-v1/execute.py --approved-plan-sha <plan-lock.json中经总控放行的sha256>
```

本阶段不运行上述命令，也不运行其IRworker/工具子命令。execute.py先验计划/新源/旧绑定/工具exe，再独占创建run-v1，永不覆盖/续跑。每case先新IR子进程（30s），再Icarus compile15s/sim10s；所有实际argv、executable SHA、前置reservation、stdout/stderr/receipt、raw/normalized、driver offer、三路verdict和计数入run。顺序并发1；最多11/11/11、1800s总软界、250MiB输出软界。每个case最多80周期，bounded drain8。超时/工具错误/parse异常/任何预期或同映射相位不符立即停止；保留已完成、当前失败和未启动slot，不重跑/补样/改判据搜索PASS。不结束其他进程、不修改代理环境，不恢复fyp自动化。

源变更导致gate拒绝，需总控重新决定，不能沿旧SHA运行新代码。执行后的evidence-lock及结果独立于准备封存，run-v1不属于阶段A包。当前准备脚本只会拒绝已存在plan，不可覆写。阶段B若完成，还必须总控独立核raw/相位/账/完整分母/源，不以harness自评放行外部任务。

## 外部任务准备关卡

此阶段A只具备“可审准备材料”，不具备“验证完成”。阶段B需要完整映射静态接受+实测合法差异通过、因果/残留破坏检出、环境/采样/不可对齐不误归功能失败、原负结果保全且异常无重试；仍须说明同作者开发、AST插桩未与未插桩run直接重放的局限。通过后仅可判断是否具备**另行准备**新外部来源与独立契约盘点的测量基础，不能自动搜新候选、冻结最终集、运行模型或生产接入。

自然错误定位效用、独立来源/参考、split及未调优性、S/D×F/R调用机会和私有反馈隔离，需要未来新任务授权/冻结；本批任何PASS不能转成模型收益。阶段A交总控一次即停，不循环派生准备轮。
