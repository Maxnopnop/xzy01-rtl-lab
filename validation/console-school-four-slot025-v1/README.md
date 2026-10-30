# 第25槽：控制台四工具现场验收

状态：包已准备、离线校验通过，等待用户在学校执行。未调用模型、未启动学校工具。四份独立包由现有console_school.pack生成，保留旧实验及学校结果。

## 1. Windows控制台

关闭旧v2窗口后，双击项目 outputs/rtl-batch/Open-Lab-v2.cmd。无需API key，不点击模型运行按钮。

点“读取新96”，选ordinal=25（Prob094_gatesv / no_rag / gpt-5.6-luna / s001）。切换“学校单例 / 回传”。本轮包已准备，不再点“打包一个案例”，避免重复创建。

点新增“载入已打包记录”，在本目录records文件夹依次选择vcs.json、xcelium.json、dc.json、genus.json即可查看相应包。每次只载入一个；切换记录不会运行EDA。可点“校验共享文件并复制命令”，或使用下方已整合的短命令。

## 2. 学校终端

当前终端目录不限；命令由bash解释，原shell可为tcsh。不要粘贴终端提示符，也不要使用here-document。

先执行只读检查：

```bash
bash "$HOME/tsclient/FYP/ECE-Console-Verify25/verify25.sh" check
```

应得到READY_FOR_FOUR_MANUAL_COMMANDS。检查包文件、Python/tcsh、四个setup、DC的.db及Genus的.lib可读性；不占用EDA许可证。

若找不到脚本，用 `ls -la "$HOME/tsclient/FYP/ECE-Console-Verify25"` 检查共享刷新。文件已在Windows的C:/Users/A/Documents/FYP/ECE-Console-Verify25；不通过换终端工作目录修复共享问题。

检查通过后，逐条执行，每条等提示符回来：

```bash
bash "$HOME/tsclient/FYP/ECE-Console-Verify25/verify25.sh" run vcs
bash "$HOME/tsclient/FYP/ECE-Console-Verify25/verify25.sh" run xcelium
bash "$HOME/tsclient/FYP/ECE-Console-Verify25/verify25.sh" run dc
bash "$HOME/tsclient/FYP/ECE-Console-Verify25/verify25.sh" run genus
```

每条只执行一个工具的一份RTL，无自动遍历、重试或模型请求。正常结束有RETURN COPIED。若为环境、许可证、超时或文件错误，先停下保留输出，不重新执行run。模拟结果为CHECK_COUNT_DIFFERENT时表明已得到结果但检查数不符，保留记录，可继续其他独立工具的预定单例。历史VCS=212、Xcelium=211、原Icarus=213均0错误，不把历史计数改成新期望。

若仅回传失败，脚本保留学校HOME结果；仅补传命令（以vcs为例）：

```bash
bash "$HOME/tsclient/FYP/ECE-Console-Verify25/verify25.sh" ship vcs
```

其他工具替换最后一个词。不要重跑run；同包在学校的目录防重复执行。

## 3. 结果回收

控制台学校页：“载入已打包记录”选records/vcs.json →“回收结果并验hash”会默认定位其共享inbox/console-return.json。重复对其他三份记录操作。界面显示校验后的状态、样本数、错误数或综合状态。

也可以在Windows PowerShell一次回收四份已存在结果（只读校验/导入，不执行EDA或模型）：

```powershell
& 'E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch\validation\console-school-four-slot025-v1\Collect-Results.ps1'
```

将学校四条结果和此汇总发回当前对话，进行日志/源码/约束/库/工具版本的最终复核。RETURN_NOT_FOUND表示尚未回传，不能当作工具失败；IMPORT_REJECTED需要先核证据，不能跳过。

## 验收口径

- VCS/Xcelium：实际版本、退出码、原RTL/TB/reference哈希、计分记录、样本完整性与差异分开核查。
- DC/Genus：实际版本、库和SDC哈希、退出码、nonce完成标记、网表与面积/时序报告。COMPLETED_REVIEW_REQUIRED表示工具返回完整产物，仍需审阅日志，不代表功能/时序签核。
- 两个综合包使用原slot25的10ns组合smoke约束；没有输入延时/驱动/输出负载，不能作正式PPA结论。Genus使用同角的Liberty文本库，DC使用编译.db。
- 本轮检验控制台真实四工具与回传链路，不扩模型样本，不修改RTL/测试，不自动增加门级仿真。

## 已完成本机检查

四包共享文件SHA匹配；学校Python语法兼容3.6；13个Bash入口语法通过；PowerShell回收入口解析通过；隐藏Tk读取336历史槽并切换四份打包记录通过。回收器在尚无学校回传时正确报告四个RETURN_NOT_FOUND。详情prepared.json、offline-check.json、bash-syntax.json、source-lock.json。修改GUI仅新增载入记录及回传文件定位，旧锁/原始实验未改；未来API放行须绑定当前源码。
