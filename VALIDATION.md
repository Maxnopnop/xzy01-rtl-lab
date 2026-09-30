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

这是自建小模块任务集的初始基线，不是公开 benchmark 成绩，也不证明复杂芯片设计正确。尚未完成真实 VCS/Xcelium、综合、形式验证或 PPA 验证。HTTP 通道与商业回传的测试使用明确标注的 mock/synthetic 数据，不计入上表的真实 LLM 次数。

完整本机证据位于 `validation/`（Git 忽略）；仓库保存去除账户和机器路径后的摘要及生成 RTL。源码、清单、向量和 RTL 在 Git 中按精确字节保留，便于与 SHA-256 对照。
