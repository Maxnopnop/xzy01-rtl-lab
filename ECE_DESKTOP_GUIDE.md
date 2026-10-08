# 本机 → ECE Horizon → 单案例仿真 → 本机验收

入口：`vdi.ece.ust.hk`。使用你已安装的 Omnissa Horizon Client 登录学校 Linux 桌面；密码只在学校登录窗口输入。本工具不保存密码、不建立 SSH，也不提交 SLURM 作业。

## 首次设置

1. 本机仅共享专用目录，例如 `E:\FYP-Transfer`。在 Horizon 设置中查找文件夹/驱动器共享选项并添加该目录；不同版本界面名称可能不同。
2. 进入 ECE 桌面后在文件管理器查找共享目录。Linux Agent 的默认候选位置是家目录下 `tsclient`，学校可以更改挂载位置或禁用共享，因此以实际桌面为准。
3. 将 ZIP **复制到学校家目录再解压**，不要直接在共享盘运行仿真。共享目录若不可见，先重新连接一次并检查设置；若仍不可用，只能采用学校允许的浏览器文件上传/下载方式，或询问 `eehelp@ece.ust.hk` 哪种文件传输方式开放。这里不假定学校支持某个上传入口。

共享功能及权限由服务器策略控制，见 [Omnissa Horizon FAQ](https://techzone.omnissa.com/resource/horizon-8-frequently-asked-questions-faqs) 和 [Linux Agent 配置说明](https://docs-be.omnissa.com/bundle/Horizon-8_2103_Setting-up-Linux-Desktops-in-Horizon/raw/resource/enus/Horizon_8_2103_Setting_up_Linux_Desktops_in_Horizon.pdf)。候选挂载目录不代表当前学校配置已经确认。

### 当前已配置的便捷路径

用户已确认 ECE LAB7 是 Linux 桌面，并提供 Horizon 设置截图，客户端已添加共享 `C:\Users\A\Documents\FYP`。已在该目录下建立 `ECE-Transfer`，放入 `ece-vcs-ready-20261008.zip`、`ece-xcelium-ready-20261008.zip` 和本指南。无需共享整个用户主目录，也无需额外添加 `E:\FYP-Transfer`。学校端仍需确认挂载成功。

当前最短操作：在学校文件管理器打开共享的 FYP → ECE-Transfer，把 VCS ZIP 复制到学校家目录并解压，进入 `ece-vcs-ready-20261008` 打开终端执行 `python3 ece_desktop.py doctor`。然后根据检查结果运行下文单案例命令。回传 ZIP 放入同一共享目录，本机 receive 的 `--zip` 使用 `C:\Users\A\Documents\FYP\ECE-Transfer\回传文件名.zip`，`--package` 使用 `exports/ece-vcs-ready-20261008`。

## 本机：打包与传入

在仓库目录打开 PowerShell。任务 ID 必须来自对应运行的 `summary.json`；可打包多个案例，但学校每次只运行其中一个。

```powershell
.\ece.ps1 pack --run-dir runs/paired-a32 --out exports/ece-vcs-demo --backend vcs --jobs m01__real_overlap__s001__control
.\ece.ps1 stage --zip exports/ece-vcs-demo.zip --shared-dir E:\FYP-Transfer
```

如需 Xcelium，另选新的输出目录并使用 `--backend xcelium`。脚本自动找到本机 Codex Python；也可以直接使用自己的 Python 3.10+ 执行 `ece_transfer.py`。包包含 RTL、测试台、向量、案例 nonce、源文件哈希、单案例 tcsh 脚本和独立 Python 助手；不包含账户配置或模型登录信息。原始导出目录留在本机，回传时用于核对。

## 学校：手动执行一个案例

在 ECE 桌面终端，进入复制到家目录并解压后的 `ece-vcs-demo`：

```bash
python3 ece_desktop.py doctor
python3 ece_desktop.py list
python3 ece_desktop.py run --case m01__real_overlap__s001__control
```

`doctor` 只检查文件与环境，不运行 EDA。Python 助手仅需要标准库，支持 Python 3.6+；学校 Python/tcsh/商业许可证的实际可用性尚待验证。每次 run 创建全新的 `results/案例ID/时间_UUID`，默认最多等待 300 秒，保留启动日志、工具日志、退出码和检查回执。**不要在共享 VDI 上编写循环执行所有案例**。

VCS 默认 setup 是 `/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc`；Xcelium 是 `/usr/eelocal/cadence/xcelium2303hf/.cshrc`。若学校路径变化，可在启动 Python 前设置 `VCS_SETUP` 或 `XCELIUM_SETUP` 环境变量。工具加载与许可证错误会保留在 `launcher.log`，不能作为设计失败。

如无 Python 3，可在一个案例目录手动执行 `tcsh run_vcs.csh` 或 `tcsh run_xcelium.csh`，然后将该案例完整目录复制回本机，并用原有 `school_bridge.py import` 接口导入。此方式不具备新助手的独立尝试目录和自动收集功能。

## 学校：收集并带回

把 run 输出的尝试目录名称填入 `--attempt`；以下 `时间_UUID` 是占位符：

```bash
python3 ece_desktop.py collect --case m01__real_overlap__s001__control --attempt 时间_UUID --out returned-vcs.zip
```

将生成的 ZIP 复制回 Horizon 共享目录。收集只带回验收所需文件，排除编译产物和巨大波形。不会触发新的仿真。每次使用新的 ZIP 名，避免覆盖。

## 本机：接收与判定

```powershell
.\ece.ps1 receive --package exports/ece-vcs-demo --zip E:\FYP-Transfer\returned-vcs.zip --out returned/ece-vcs-first
```

查看输出目录的 `import-report.json` 和原始包的 `commercial_results.json`。判定校验源码哈希、nonce、检查数量、工具日志和退出码；许可证不可用为 `ENV_ERROR`，源码被修改为 `EVIDENCE_ERROR`，缺少结果不能算通过。没有回传的案例仍未验证。回传 ZIP 拒绝路径穿越、符号链接、重复条目及不属于包的文件，并限制解压总量。

本机模拟回传测试仅验证运输和判定代码，不证明 VCS/Xcelium 在 ECE 已运行。首次真实验收至少保留：`doctor` 输出、完整 ZIP、工具版本和一次实际 PASS/FAIL 结果。这里没有远程主机身份认证，回执是用户提供的证据。

## 本轮小实验记录

2026-10-08 新建 `runs/ece-pilot16-20261008`，计划两模型 × 四张错误表 × 两条件 × 一次重复，最多 16 次调用。最初两项模型请求返回 403 Forbidden；用户开启学校 VPN 后，再提交两项尚未执行的任务，仍返回同样的 403。共占用 4 个预算槽位、0 份有效模型输出，剩余 12 项暂停提交。不能由此估计反馈方法的效果，也没有将失败重新计入新预算。已有历史样本用于本次学校传输准备；该准备不替代新实验。

连接完成后，下一步只需确认学校桌面能否看见专用共享目录，再运行 `doctor`。如果 Horizon 持续显示“正在连接”，当前截图只能说明会话尚未建立；需进一步检查学校网络/客户端连接状态，不能据此断定许可证问题。
