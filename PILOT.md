# 两模型 pilot：60 次生成

实验配置保存在 `experiments/pilot60.json`：`gpt-5.6-sol`、`gpt-5.6-terra` 各 10 题 × 3 次，共 60 次生成尝试。模型依据本机已登录 Codex CLI 的模型目录选择；沿用同一供应商通道以先验证研究流程，不声称跨供应商多样性。

冻结 `dev10-v1` 的来源、提示词、测试、向量及代码；每题使用同一提示词独立生成三次，reasoning=low，生成超时 180 秒，并发最多 2，无自动修复、无测试反馈、无工具访问。CLI 没有设置 temperature、采样 seed 或输出 token 上限；按原样记录未指定，不宣称三个样本统计独立或 token 成本完全相同。模型名称是请求 ID，CLI 不提供可核实的后端快照 ID。

每个模型最多 30 次调用预留，总上限 60；失败也占槽位，不悄悄补抽。按 10 题一个样本轮次执行，模型顺序为 A→B、B→A、A→B。API/环境异常时停止后续 block 并保留证据。续跑跳过已结束槽位；如需替换失败尝试，应新建另一个实验并报告原因，不能覆盖 baseline。

## 本机运行

在仓库根目录 PowerShell：

```powershell
# 初始化是只建计划，不调用模型。
.\pilot.ps1 init --run-dir runs\pilot60
# 执行 60 次计划内调用；重复执行只处理缺失槽位。
.\pilot.ps1 run --run-dir runs\pilot60
# 对已经保存的同一份 RTL 做 Yosys 综合，不重新生成 RTL。
wsl -d Ubuntu -- python3 pilot.py synthesize --run-dir runs/pilot60
.\pilot.ps1 report --run-dir runs\pilot60
Invoke-Item runs\pilot60\pilot-report.html
```

前两步使用 Windows 已登录的 Codex CLI 和 Windows Icarus，综合步骤完全在本机 WSL 内执行。Windows 与 WSL 是不同工具环境，版本与哈希分别记录。综合保留独立 `synthesis-review` 结果，并同时绑定原始 result.json 与 RTL 的哈希；修改生成文件会被拒绝。未完成生成前不执行综合重放，防止与生成过程竞争。

WSL 安装工具：`sudo apt-get install iverilog yosys`。Linux 已有独立 Codex 登录时也可将全流程放在同一 Linux 环境。Windows 原生 Yosys 可通过 `batch.py --synthesis yosys --yosys <path>` 接入；不通过杀死 wsl.exe 来冒充 Linux 进程树清理。

先试一轮可用 `--max-blocks 1`，即第一个模型的第一组 10 题；这属于原 60 次计划，不额外分配 smoke 调用。所有模型结果都归档，包括功能失败与综合失败。

## 结果与解释

`pilot-summary.json/csv` 和 `pilot-report.html` 汇总：计划/完成、真实生成次数、调用预留、功能通过、综合通过、联合通过、每题三次结果及 token usage。功能通过的分母为全部 30 个计划槽位；综合/联合通过同样保留失败槽位。工具报错和电路错误分别记录，不把环境失败算成“已生成但功能错误”。

报告实现按 benchmark 分层、以整题为单位的成对 bootstrap：每次在每个来源的 5 题内有放回抽取 5 题，三次生成整体跟随该题，两个模型使用同一组抽样。固定 5,000 次、seed=20260930，输出模型均值与 B−A 差值的 95% percentile 区间。只有相应阶段全部完成才生成区间。10 题样本很小；全通过时区间可能退化为 [1,1]，不能据此推断真实泛化正确率为 100%。指标为固定样本平均通过率，不是官方 pass@k。

综合采用 `read_verilog -sv → hierarchy → proc/check → synth -noabc → check → stat/write_json`。记录通用单元和 latch 数，没有工艺库、时钟约束、布局布线，不能当作 PPA，也未做综合网表功能等价证明。

扩至四模型时复制配置到新文件，设置四个明确 model ID，再以 `--config` 初始化新的实验目录（120 次，不能在旧 60 次实验里加模型）。兼容 API 访问仍由 `batch.py --mode live` 提供；引入另一供应商前应明确其模型、认证、采样字段和预算，并另建同任务比较计划。

学校 VCS/Xcelium 继续使用 `school_bridge.py` 导出单个案例、VDI 手动运行和结果导入，不自动向共享 VDI 提交批任务。

CLI 的显式模型参数与非交互行为见 [OpenAI 官方模型文档](https://learn.chatgpt.com/docs/models)及[非交互文档](https://learn.chatgpt.com/docs/non-interactive-mode)。
