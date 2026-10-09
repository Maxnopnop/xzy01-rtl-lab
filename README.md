# XZY01 RTL Lab

按钮窗口：双击 **Open-Lab.cmd**。可配置模型、隐藏输入 API 密钥、粘贴完整原文提示词、设置预算、启动实验及收取学校结果。打开窗口不调用 API。

统一入口：[完整工具清单与一键流程](FYP_ONE_COMMAND.md)。支持完整提示词原文输入、本机 API→Icarus→Yosys→打包、学校共享目录/Git 单案例运行及结果回传。

多模型 API 入口：[CSV 配置与批量调用指南](MODEL_PLATFORM.md)。`models.ps1 template/check/prepare/run/report`；集中填写基础地址、模型 ID 和密钥环境变量名，预览与建任务均不调用 API。

项目总览：[完整流程与阶段总结（2026-10-09）](FYP_FLOW_SUMMARY.md)。

日常统一入口：[历史实验 → 学校单案例菜单 → 自动回传 → 本机报告](ECE_WORKFLOW.md)。本机 `ece.ps1 history/prepare/ingest/status`，学校 `ece_menu.sh`。已准备 178 份历史 RTL 的两工具菜单，共 356 个待验证项；本机 178 份复验结果全部与原实验一致，不产生新模型调用。

学校商业仿真验证现已完成一例 **Icarus / VCS X-2025.06-SP1 / Xcelium 23.03-s004** 对照：三工具使用相同源文件，均通过 1840 次检查、0 错误。见 [Xcelium 实际验收证据](evidence/ece-xcelium-smoke-20261008/result.json) 和 [学校操作指南](ECE_DESKTOP_GUIDE.md)。此为单案例流程验收，不是整个开发集的商业工具复验。

学校桌面接入：[Horizon 单案例传输与回传指南](ECE_DESKTOP_GUIDE.md)。入口 `vdi.ece.ust.hk`；使用 `ece.ps1` 打包/传入/接收，在 ECE 终端使用包内独立 `ece_desktop.py` 运行一个案例并收集日志。2026-10-08 已完成一例真实 VCS X-2025.06-SP1 验收：1840 次检查、0 错误，与 Icarus 一致；[证据](evidence/ece-vcs-smoke-20261008/result.json)。Xcelium 同例也已实际验证通过。

最新验证：[公开检查盲点与错误定位](MUTATION_FINDINGS.md)。零新增模型调用，系统枚举 163 种单处故障，发现原公开检查漏检 30 种；独立新版公开 profile 增加 12 个例子后覆盖这批全部故障，25 格实际 Icarus 诊断校准通过。此为开发内工具验证，不改变下述模型实验分数。

最新完成：[固定错误表的 32→64 次配对扩展](PAIRED_FINDINGS.md)。96 个预算槽位取得 94 份真实 RTL（另 2 次系统睡眠超时），94/94 综合通过，89/94 功能通过；自然错误与人工注错分开报告。新增四个开发题族、两个未进行模型实验的候选保留题，保留全部结果及 [可执行证据审计](paired_audit.py)。

用于 FYP 的本机实验流程：**规格 → LLM 生成 RTL → 固定独立测试 → Icarus 编译/仿真 → Yosys 综合 → CSV、JSON、HTML 结果**。

新增：已固定来源的 **[10 题开发集](benchmarks/dev10/README.md)**（VerilogEval 5 + RTLLM 5），以及 **[两模型 × 10 题 × 3 次 pilot](PILOT.md)**。原有 20 个自建任务继续用于工具链回归，与公开来源开发题分开记录。

60 次真实 pilot 已完成：两模型各 24/30 仿真通过、30/30 通用综合通过。详见 **[结果与 FYP 位置](PILOT_FINDINGS.md)**，包含失败原因、统计限制和仍待完成的最终测试集。

后续 **[48 次调用的 FSM 实验](FSM_FINDINGS.md)** 已完成：普通计划 7/8、状态表 7/8、状态表＋检查 8/8，24/24 综合通过。已定位一例规格到状态表的重叠检测错误；检查组初始表全部正确，因此尚未验证反馈的纠错增益。见 [实验协议](FSM_STUDY.md) 和 [文献对照](FSM_LITERATURE.md)。

提供 20 个自建电路任务、每题多样本、1–16 个有界并行工作进程、断点续跑、调用上限、逐阶段日志，以及学校 VCS/Xcelium 手动复核接口。默认并发 2，建议本机离线仿真用 4。这是研究起步用的本地任务集，不是 VerilogEval，也不是芯片完整签核流程。

## 1. 环境与快速开始

- Python **3.10+**，只用标准库，不需要 pip 安装依赖。
- Icarus Verilog 的 `iverilog` 和 `vvp`。
- Windows、WSL2/Linux；真实 Codex 调用还需已安装且已登录的 Codex CLI。
- 本机 Windows 已发现 `D:\iverilog\bin`。`run.ps1` 优先使用 `RTL_LAB_PYTHON` 或 PATH 上的真实 Python，也支持已安装的 Codex Python 运行时。Windows 商店占位符会被跳过。
- 换电脑后，安装独立 Python、Icarus，将它们放入 PATH，或通过 `--iverilog` / `--vvp` 指定完整路径。

克隆仓库并进入目录，然后在 PowerShell 执行：

```powershell
# 第一次：建立 20 题 × 2 次的离线计划
.\run.ps1 init --run-dir runs\offline-demo --mode offline --samples 2
# 实际执行；重复此命令会跳过已完成的任务
.\run.ps1 run --run-dir runs\offline-demo --workers 4
# 打开本地报告
Invoke-Item runs\offline-demo\report.html
```

若当前 PowerShell 策略阻止脚本，可显式运行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 ...`；该设置仅作用于这次进程。也可直接使用 `python batch.py ...`，无需修改执行策略。

Linux/WSL 等价命令：

```bash
python3 batch.py init --run-dir runs/offline-demo --mode offline --samples 2
python3 batch.py run --run-dir runs/offline-demo --workers 4
```

离线默认使用 `examples/correct` 人工样例。重复离线样例用于检查调度可靠性，**不能解释为独立模型样本或模型正确率**。

## 2. 真实 LLM 生成与批量仿真

沿用已验证的 `gpt-5.6-sol`，通过已有 ChatGPT 登录的 Codex CLI 运行：

```powershell
codex login status
.\run.ps1 init --run-dir runs\codex-40 --mode codex --model gpt-5.6-sol --samples 2 --max-calls 40
.\run.ps1 run --run-dir runs\codex-40 --workers 2
```

这会计划 **20 题 × 2 次 = 40 个真实生成样本**，使用账户的 Codex 用量。`--samples 5` 即 100 个样本，需同时将调用上限设为 100。不要把账户订阅理解为无限使用额度。

模型在每个样本的空工作目录中运行，不提供 testbench 或参考答案；禁用 shell、浏览器、应用、插件和子代理等功能，检测到工具调用则拒收为本实验样本。模型标识记录的是明确传入的请求值，CLI 没有返回后端快照时不虚构快照。Codex 模式默认 reasoning=low；temperature/seed/token 上限没有发送，记录为未指定。

使用自己的兼容 HTTP 服务时：

```powershell
$env:LLM_BASE_URL = 'https://你的服务域名/v1'
$env:LLM_MODEL = '你的模型标识'
$secretInput = Read-Host 'API key（仅在本机输入）' -AsSecureString
$env:LLM_API_KEY = [System.Net.NetworkCredential]::new('', $secretInput).Password
.\run.ps1 init --run-dir runs\api-20 --mode live --samples 1 --max-calls 20
.\run.ps1 run --run-dir runs\api-20 --workers 2
Remove-Item Env:LLM_API_KEY
```

HTTP 通道使用 Chat Completions 兼容协议；支持本地兼容服务，以 `--allow-anonymous` 显式允许无密钥。不自动配置供应商，不自动购买额度，不跟随 HTTP 重定向。该通道的模拟测试不代表真实服务验证。

## 3. 扩大规模、续跑与重试

```powershell
# 先只做 4 个新任务，再检查日志
.\run.ps1 run --run-dir runs\codex-40 --workers 2 --max-jobs 4
# 继续剩余任务；不会重复生成已有最终结果
.\run.ps1 run --run-dir runs\codex-40 --workers 2
# 明确重试接口/环境失败，并提高整个实验的总调用上限
.\run.ps1 run --run-dir runs\codex-40 --retry-status API_ERROR,ENV_ERROR --max-calls 44
# 仅重新生成报告，不调用模型
.\run.ps1 report --run-dir runs\codex-40
```

- 每个任务有固定 ID，例如 `fifo4x8__s002`，每次尝试新建 `attempt_001`、`attempt_002`，保留历史证据。
- 默认不重试已完成失败，避免额外调用和改变统计口径。未完成/被中断的任务可以续跑。
- 模型调用上限采用保守的“尝试开始即预留”计数：即使随后网络失败或崩溃，也不退回预留额度。CLI 自身可能内部重连，计数不是底层 HTTP 请求数或精确计费单位。
- 若在模型生成后、结果落盘前中断，续跑可能重新生成该样本并消耗一次新额度；旧尝试仍保留。用 `--max-calls` 明确授权额外尝试。
- Ctrl+C 请求停止，清理正在运行的子进程，保留结果；下次用相同命令续跑。
- 同一实验只能有一个调度器写入；操作系统锁在进程退出时自动释放。
- 修改核心代码、题目/向量或仿真器后必须新建实验目录。结果可重新汇总，但不允许混合不同环境继续跑同一个实验。
- `run` 返回 0 表示全部计划样本通过，1 表示存在失败或未完成，2 表示配置/执行环境问题。因此 `--max-jobs` 的部分完成返回 1 是正常的。

CLI：`python batch.py --help`、`python batch.py init --help`、`python batch.py list`。

## 4. 题目与验证范围

| 类型 | 任务 |
|---|---|
| 基本组合逻辑 | adder8、encoder4、mux8、decoder3、parity8 |
| 运算与编码 | alu8、shift8、signedcmp8、popcount8、gray8、saturating8、leadingzero8 |
| 时序逻辑 | counter4、dff8、shiftreg8、updown8、edge_detector、pulse_div4 |
| 状态与存储 | sequence101（重叠序列）、fifo4x8（边界及指针回绕） |

一轮 20 题共 **107,368 次输出检查**。小输入域题目穷举；其他题目采用明确的边界条件、固定种子伪随机向量和 Python 参考模型。时序任务检查上升沿之后的输出以及边沿之间的保持，以识别同步/异步复位错误。FIFO 测试覆盖满/空、同时读写、复位、连续读写和指针回绕。

`tasks/manifest.json` 固定规格、模块名、检查数、TB 与向量哈希。`build_tasks.py` 可确定性重建新增题目；原有三题由独立手写 TB 保留。`examples/wrong` 为每题提供一个明确错误实现，用于确认测试能发现错误。

仿真 PASS 表示通过这些固定用例，不是所有时序上的数学证明。现支持独立 Yosys 通用综合与结构检查；尚无形式等价、PPA 或实际芯片签核。重复使用固定测试集不会增加测试覆盖率。

在已安装 Icarus/Yosys 的 WSL 内验证开发集：

```powershell
wsl -d Ubuntu -- python3 batch.py init --run-dir runs/dev10-audit --suite dev10 --rtl-dir benchmarks/dev10/reference --synthesis yosys
wsl -d Ubuntu -- python3 batch.py run --run-dir runs/dev10-audit --workers 4
```

`status` 保留功能仿真结果；`synthesis_status` 单独记录 `SYNTH_PASS/FAIL/TIMEOUT/ERROR`，`joint_pass` 表示两项同时通过。未请求综合时联合字段只反映已请求的仿真阶段，不能声称完成了综合。综合启用时退出码 0 要求所有样本联合通过。`synthesis.py --run-dir <已有实验>` 可在 WSL 对保存的 RTL 单独复核，既不重新调用模型，也不修改原仿真记录。

## 5. 判题和证据

只有同时满足以下条件才 PASS：编译成功、仿真正常退出、固定 TB 写出唯一且匹配本次 nonce 的完成凭据、执行检查数完全一致、错误数为零。模型打印的 PASS 不作为依据。

主要状态：`PASS`、`FUNCTION_FAIL`、`COMPILE_FAIL`、`TIMEOUT`、`API_ERROR`、`ENV_ERROR`、`EXTRACTION_ERROR`、`RTL_REJECTED`、`SIM_ERROR`、`INTERRUPTED`。许可证/API/环境问题独立于电路功能失败。

```text
runs/<实验>/
  plan.json              固定任务、配置、代码哈希、调用上限
  environment.json       Python、工具版本、二进制哈希
  summary.csv/json        样本结果与分类
  report.html            可离线打开的结果页面
  jobs/<题目__样本>/
    result.json           最新一次尝试结果
    attempt_001/
      started.json       调用预留记录
      worker.log
      001_<题目>/         提示词、原始输出、RTL、固定 TB/向量、编译/仿真日志
```

总览使用全部计划样本作为分母，显示未完成和环境失败；不通过删除失败提高成绩。显式重试后主表反映最后一次结果，所有尝试和 token usage 仍保留；比较研究 baseline 时应使用没有反馈/重试的新实验。没有实现或声称标准 benchmark pass@k 指标。

## 6. 学校专业 EDA 接口

目前学校共享 ECE VDI 不支持 SSH、批量 EDA 或调度器。为此只提供**选定案例的导出、手动单次运行、证据导入**，不自动连接学校或执行批量任务。

```powershell
python school_bridge.py export --run-dir runs\codex-40 --out exports\vcs-check --backend vcs --jobs adder8__s001,fifo4x8__s001
```

通过 VDI 共享文件夹把整个包复制到学校 Linux 家目录。一次进入一个案例目录，运行：

```csh
tcsh run_vcs.csh
```

使用 Xcelium 时导出 `--backend xcelium`，执行 `tcsh run_xcelium.csh`。脚本使用现有学校初始化路径；管理员更改路径时可通过 `VCS_SETUP` 或 `XCELIUM_SETUP` 环境变量覆盖。

将完整案例文件夹复制回本机后：

```powershell
python school_bridge.py import --package exports\vcs-check --returned returned\vcs-check
```

导入会核对原始源码/向量哈希、nonce、检查数、退出码、工具版本与日志，并保存独立的 `commercial_results.json`。不能把合成测试凭据当作学校运行记录。**这些脚本和导入器已本地验证接口逻辑，但尚未在学校 VCS/Xcelium 上实际运行。** 手动运行没有自动墙钟超时，需要在 VDI 中观察并按需停止。

未来获准使用 SSH 或专用服务器后，可增加 transport 层上传、执行、取消和下载；仍复用同一任务规格与判题协议。详见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 7. 测试、GitHub 和后续开发

```powershell
python -m unittest -v test_lab test_batch test_dev test_fsm test_paired test_paired_audit test_mutation
```

测试包括正确/错误 RTL、缺失/伪造凭据、语法错误、无限循环超时、进程树清理、并行续跑、重复启动锁、输入变化拒绝、人工商业工具回传协议，以及模拟 HTTP 异常。HTTP 和商业回传夹具均明确标注为 synthetic/mock，不计入模型或商业 EDA 成绩。

GitHub Actions 在 Linux 上只执行离线测试，不调用模型、不需要 API key。实际验收状态见 [VALIDATION.md](VALIDATION.md)。

仓库保留源码、规格、固定 TB/向量、测试、中文文档和去除机器路径的验收摘要；`.gitignore` 排除真实运行日志、模型原始回复、生成二进制和本地密钥。完整运行证据保留在本机。模型生成的可综合 RTL 抽样可另行整理提交，但不要提交账户日志。

## 8. 实现边界与参考

当前任务仅支持受限单模块 RTL。生成结果禁止 include、额外模块、层级访问、系统文件 IO/退出任务等；这不是执行任意恶意 HDL 的强隔离沙箱。平台有超时和日志大小上限，没有硬内存配额；未来接收第三方 HDL 时应另配容器/虚拟机隔离。

- [Codex 非交互调用](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Icarus 编译参数](https://steveicarus.github.io/iverilog/usage/command_line_flags.html)
- [vvp 运行参数](https://steveicarus.github.io/iverilog/usage/vvp_flags.html)
- [VerilogEval](https://github.com/NVlabs/verilog-eval) 与 [RTLLM](https://github.com/hkust-zhiyao/RTLLM)：本仓库固定 5+5 适配开发题，上游 MIT 许可与原始文件随库保存；后续最终测试集单独审计。
