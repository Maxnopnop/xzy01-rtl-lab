# 实际验收记录

会话日期：2026-09-30（Asia/Shanghai）。原始进程时间保留在本机运行日志中。

| 验证项目 | 实际结果 |
|---|---|
| 20 题 × 2 次人工正确样例 | 40/40 PASS，Windows Icarus |
| 20 题故意错误实现 | 20/20 FUNCTION_FAIL，符合预期 |
| 20 题 × 10 次离线并行压力测试 | 200/200 PASS，4 个并行工作进程 |
| 20 题 × 2 次真实 Codex 生成 | **40/40 PASS**，请求模型 gpt-5.6-sol，reasoning=low，最多 2 个并行样本 |
| 完成后再次运行相同真实实验 | 已完成任务全部跳过，调用预留仍为 40 |
| Windows 回归 | 16 项整组测试通过，新增调用上限测试单独通过，共 17 项 |
| WSL Ubuntu 回归 | 16 项整组测试通过，新增调用上限测试单独通过，共 17 项 |
| GitHub Actions 干净 Linux 环境 | 17/17 测试通过；[运行记录](https://github.com/Maxnopnop/xzy01-rtl-lab/actions/runs/36723549380) |
| VCS/Xcelium 导出 | 已导出真实模型生成的 adder8 与 fifo4x8 两类案例 |
| 商业工具回传接口 | 本地合成凭据测试通过；尚未实际登录学校执行商业工具 |

真实实验一共执行 **214,736 次输出检查**（107,368 × 2），没有让模型查看测试程序，没有反馈修复，没有手动替换生成 RTL。两次生成使用相同规格和固定测试，不构成新的测试覆盖范围。

每个结果的 RTL 哈希、测试哈希、请求模型、usage、耗时及状态见 [evidence/live_summary.json](evidence/live_summary.json)。40 份生成 RTL 位于 `evidence/generated/sample_001` 和 `sample_002`；准确发送的提示词位于 `evidence/prompts`。CLI 自身内置系统上下文不由本项目控制，服务端模型快照未返回，不能把请求的模型名称当成已验证的快照 ID。

CLI 记录的累计 usage 为 input_tokens=341608，cached_input_tokens=199168，output_tokens=4752，reasoning_output_tokens=0。缓存字段属于输入 token 的细分，不能再次加到输入总量；这些数值不是货币费用估计。

本次 Windows 仿真器报告 `Icarus Verilog version 12.0 (devel) (s20150603-1539-g2693dd32b)`，WSL 报告 `12.0 (stable) ()`。分别记录，不将两者混为相同二进制。真实模型生成与 200 次压力测试使用 Windows 工具。

## 不调用模型，复核保存的真实生成代码

```powershell
.\run.ps1 init --run-dir runs\replay-sample1 --mode offline --rtl-dir evidence\generated\sample_001 --samples 1
.\run.ps1 run --run-dir runs\replay-sample1 --workers 4
```

该结果标记为 offline，因为此时是重放已有代码，不是再次调用模型。第二组使用 `sample_002`。

## 解释范围

上面的历史结果是自建小模块任务集的初始基线，不是公开 benchmark 成绩，也不证明复杂芯片设计正确。现已补充下述 Yosys 通用综合；尚未完成真实 VCS/Xcelium、形式验证或 PPA 验证。HTTP 通道与商业回传的测试使用明确标注的 mock/synthetic 数据，不计入真实 LLM 次数。

完整本机证据位于 `validation/`（Git 忽略）；仓库保存去除账户和机器路径后的摘要及生成 RTL。源码、清单、向量和 RTL 在 Git 中按精确字节保留，便于与 SHA-256 对照。

## 2026-09-30：综合和正式开发集

| 新增验收 | 结果 |
|---|---|
| Yosys 0.52，本机 WSL Ubuntu | 已安装并实际执行，generic synth -noabc |
| 20 个自建参考实现 | 20/20 仿真与综合联合通过 |
| 之前保存的 40 份真实生成 RTL | 40/40 综合通过，新增模型调用 0 |
| dev10：VerilogEval 5 + RTLLM 5 | 10/10 参考实现仿真与综合联合通过 |
| dev10：每题 1 个故意错误实现 | 10/10 FUNCTION_FAIL；均能综合，验证了综合不能替代功能测试 |
| 上游来源审计 | 30 份规格/参考/TB 对照固定 Git commit；除 Windows checkout 换行外内容相同 |
| Windows 回归 | 原 17 项 + 新增 5 项通过；2 项原生 Yosys 测试在 WSL 执行 |
| WSL 回归 | 原 17 项通过，新增 7 项通过（修复跨平台排序后重跑新增整组） |

验收摘要和逐 RTL 综合信息见 [evidence/development_audit.json](evidence/development_audit.json)。综合失败、超时、冲突驱动、无法推断单一时钟结构的测试已实际运行。参考与 mutant 只用于判题器验收，不属于模型采样结果。

一轮 dev10 有 140,430 次固定输出检查。来源、适配和 final 排除规则见 [开发集说明](benchmarks/dev10/README.md)。最终 40 题尚未选择/审计。两模型 60 次 pilot 的执行方式和统计口径见 [PILOT.md](PILOT.md)。

## 已完成的两模型 pilot

实际新增 60 次真实生成：gpt-5.6-sol 与 gpt-5.6-terra 各 30 次，均 24/30 仿真通过、30/30 综合通过、24/30 联合通过。sol 有 6 次编译失败；terra 有 3 次编译失败及 3 次功能失败。全部槽位有结果，真实生成计数和调用预留均为 60，没有修复或额外调用。

详细失败分析、置信区间和 FYP 对照见 [PILOT_FINDINGS.md](PILOT_FINDINGS.md)。这 60 次与之前自建任务的 40 次是两套不同任务的独立实验，不合并成一个 benchmark 分数。

新增离线回归共 **24 项**，GitHub 干净 Linux 环境全部通过：[CI 记录](https://github.com/Maxnopnop/xzy01-rtl-lab/actions/runs/36728142866)，验证代码 commit `51de2cf`。该 CI 不调用模型。

实验结束后的 CSV 换行修复已在 Windows 重跑全部 24 项：22 项通过，2 项需原生 Yosys、由 Linux/WSL 执行。CSV 验证为表头加 60 行、无空白行；重新输出前后的 pilot JSON 完全一致，未改变实验成绩或调用次数。

## 2026-10-01：固定错误 IR 的配对扩展

冻结生成代码 `9c2a895`：Windows 41 项回归（39 通过、2 个原生 Yosys 项转 WSL），WSL 41/41 通过；该提交 GitHub CI [36750502858](https://github.com/Maxnopnop/xzy01-rtl-lab/actions/runs/36750502858) 通过。

实际预留/启动 32+64=96 次，收到 94 份 RTL；系统自动空闲睡眠导致 2 次未知结果超时，未重试、未退款。恢复只运行尚未启动的槽位，偏差单独记录。功能 89/94，通过综合 94/94。两个没有 RTL 的槽位综合为 NOT_RUN，不伪造成功。

`paired_audit.py` 在 Windows 和 WSL 对 682 个证据文件核验通过，检查源码/计划/题库锁、提示词、回复、RTL、综合源结果绑定、CSV 行数、调用上限及候选保留题未参与模型实验。两项新审计测试在 Windows 通过。GitHub 工作流包含完整 43 项测试及这次全部证据审计，且不调用模型。

详情：[结果报告](PAIRED_FINDINGS.md)、[机器可读审计](evidence/paired-analysis.json)、[睡眠恢复偏差](PAIRED_EXECUTION_NOTE.md)。学校配对案例包已在本机导出，尚未在 VCS/Xcelium 上实际运行。

本轮结果提交 `88726c896eebb36a6c9dab32d0c1912c1e1df22c` 的 [GitHub CI 36774716313](https://github.com/Maxnopnop/xzy01-rtl-lab/actions/runs/36774716313) 已通过：43 项离线测试和全部配对证据审计成功。后续文档收尾不改变生成代码或原始实验数据。
