# 日常实验与学校仿真工作流

现有真实验收：同一 FSM 的 Icarus、VCS X-2025.06-SP1、Xcelium 23.03-s004 均完成 1840 次检查、0 错误。新菜单沿用这两套商业工具脚本；菜单和自动回传经过本机/WSL 测试，菜单本身仍待学校第一次实际使用。

## 本轮大规模本机验证

- 178 份保存的模型 RTL 全部重新用 Icarus 仿真：159 PASS、10 FUNCTION_FAIL、9 COMPILE_FAIL，178/178 与原始结果一致。预期失败保留，不改成通过。
- 来源：60 份两模型 pilot、24 份 FSM 实验输出、94 份固定错误表配对输出。它们是历史输出复验，不是 178 次新模型生成。
- 重新执行 163 种单处 FSM 故障校准、5 个正确参考和 25 格错误定位校准；新增模型调用 0。公开检查覆盖率来自开发内拟合，不是保留测试集泛化效果。
- 4 个 403 调用槽位和 2 个历史超时没有 RTL，不进入复验/学校包；尚未调用的 12 项也未执行。
- 导出 10 个包（5 组历史运行 × 2 个工具），共 356 个“案例 × 工具”待验证项。这是待选菜单，不会在学校自动循环仿真。只有已回传的新尝试才填入商业结果；过去的一例 PASS 不会替新包填分。

## 现在只需要两个入口

学校共享目录：本机 `C:\Users\A\Documents\FYP\ECE-Transfer`，学校通过已验证的 `~/tsclient` 挂载访问。在学校终端粘贴：

```bash
bash -c 'find "$HOME/tsclient" -maxdepth 6 -type f -name ece_menu.sh -exec bash {} \; -quit'
```

输入运行包编号（标签区分实验/模型和 VCS/Xcelium），查看 doctor，然后输入**一个案例编号**。输入 0 退出。一次菜单启动最多调用一个 EDA 仿真，默认 300 秒超时；不要用循环包裹菜单或提交全部案例。

脚本自动复制到学校家目录的新会话目录，使用绝对路径启动 tcsh，收集当前尝试的源码、向量、日志、版本、退出码与回执，并将 ZIP 和来源 sidecar 放入共享目录 `inbox`。不再手填 attempt、执行 collect 或手工复制 ZIP。失败/超时也会收集，避免把运行结束当作功能通过。

返回本机，在仓库 PowerShell 执行：

```powershell
.\ece.ps1 ingest
.\ece.ps1 status
```

打开 `workflow/report.html`，或查看 `workflow/status.csv`、`workflow/status.json`。导入按原始包哈希、来源案例、nonce、源码、执行记录和工具日志判定；每次尝试单独保留。同一 ZIP 重复导入自动跳过，不覆盖旧尝试。`ingest` 的退出 0 表示文件导入有效，实际 PASS/FAIL 以报告为准；无回传为 NOT_RUN。

## 共享目录暂不可写

学校脚本保留 `会话目录/运行包/outbox`，打印补传命令。进入那个运行包目录后运行：

```bash
python3 ece_desktop.py ship --return-dir /实际共享路径/FYP/ECE-Transfer/inbox
```

ship 只传输已收集文件，不会重新启动 EDA。相同文件可重复补传，不同内容的同名文件拒绝覆盖。学校断开/主机重启导致进程消失时，不保证自动收集完成；已有会话/results 和 outbox 留在家目录，可查日志后恢复。

## 添加之后的实验

本机查看可导出的历史任务：

```powershell
.\ece.ps1 history
```

详细 job_id 在 `workflow/history.json`。新增运行先使用原有 batch/fsm/paired 脚本执行生成、Icarus 和已有综合流程；新菜单不发起模型调用，不绕过其预算、源码锁和基准分离机制。原来的模型服务 403 问题仍独立存在。

按具体案例打包两套工具：

```powershell
.\ece.ps1 prepare --run-dir runs/paired-a32 --jobs m01__real_overlap__s001__control --backends vcs,xcelium
```

导出一份运行里所有保留 RTL 供学校手动选择：

```powershell
.\ece.ps1 prepare --run-dir runs/paired-b64 --all-retained
```

这里只在本机批量复制/打包，学校仍逐次手动选一例。支持 `--shared-dir` 更换共享目录。Python 入口 `ece_workflow.py --state-dir 新目录 ...` 可隔离另一个实验工作台；状态目录和打包原件必须保留，接收时需要原始 nonce/哈希。学校脚本需要 Python 3.6+、tcsh；本机工具需要 Python 3.10+。

## 保存和验收边界

GitHub 保留代码、中文指南和整理后的验证摘要；`workflow/`、原始 `runs/`、`validation/` 和共享 ZIP 是本机数据，不自动提交账户/工具日志。完成时另存工作台与本轮原始验证 ZIP；后续本机接续保留这些目录即可。换电脑时要恢复数据并调整原始包路径，单独克隆代码不会恢复本机 registry/nonce。

大规模复验不扩大新模型样本数，也不表示 356 个商业工具项已完成。Windows 完整回归当前的本地 HTTP mock 两项受系统代理影响（loopback 未绕过代理）；Linux/WSL 和 GitHub CI 用于完整回归，Windows 实际 Icarus 复验及新增菜单/运输测试单独通过。未修改系统代理或冻结的旧实验代码。

`shutdown_native.ps1` 默认仅检查权限。实际关机须显式 `-Execute` 且提供测试/同步/归档全部完成的 receipt；通过 Windows `ExitWindowsEx` 正常关机，不使用强制标志。未保存程序可能阻止关机，脚本保留调用状态，不保证系统已关机。
