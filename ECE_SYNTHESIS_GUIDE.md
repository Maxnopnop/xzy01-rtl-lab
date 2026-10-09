# Design Compiler / Genus 接入与单案例综合

依据 [学校实际启动记录](ECE_SYNTHESIS_STARTUP.md)，新增 DC X-2025.06-SP2 和 Genus 21.14-s082_1；两个环境脚本已写入接入模块。启动记录不是综合结果。目前还没有确认 FYP 标准单元库和 SDC，默认明确阻止实际综合。

## 窗口操作

重新双击 **Open-Lab.cmd**，进入 **4 学校综合 DC / Genus**。

1. 选择 dc 或 genus，填写学校库的绝对路径，每行一个。DC 用 `.db`，Genus 用 `.lib` 或 `.lib.gz`。软件和库文件始终留在学校，不打包进 GitHub。
2. 填写工艺角标签，选择本机已审核的 SDC，并勾选核对框。两个工具分别保存配置。标签只是记录说明，不会自动设置电压温度；必须核对库自身的角及报告。
3. 选择已有实验的一个原始 RTL 样本，点击“生成单案例学校包”。它保留原 RTL、原结果和原计划的哈希；不重新生成或修改 RTL。
4. 点击“复制学校综合命令”，在已登录 ECE Linux 桌面的终端粘贴，选一个包。先检查库、环境和 SDC，满足条件才启动该工具；一个包只有一个设计和一个工具。
5. 学校脚本将日志、网表、输出约束和报告复制到共享 inbox。本机点击“收取综合结果”和“综合报告”。第三页“更新汇总报告”也会显示独立的 dc、genus 列。

缺库时允许生成 **BLOCKED_PREREQUISITES 草稿包**，方便验证传输和查看缺项；学校不会因草稿包启动综合。补齐配置后应重新打包，旧包保持冻结，不在学校直接修改它。

## 查询可读库

在学校终端执行，只读、最多30秒、显示前100个候选：

窗口第4页“复制查库命令”也提供同一条命令。

```bash
bash -c 'timeout 30s find -L /usr/eelocal /staff/ee/dept/public -maxdepth 7 -type f \( -iname "*.db" -o -iname "*.lib" -o -iname "*.lib.gz" \) -readable -print 2>/dev/null | head -n 100'
```

没有输出不代表没有库，可能是目录、深度或权限。不要用 sudo 或修改共享目录权限。候选文件需要由导师/学校确认使用范围，以及对应的数字标准单元工艺角；工具内部文件或不相关数据库不应直接当作项目库。

## 学校一行入口

共享 `C:/Users/A/Documents/FYP` 后，入口位于 **ECE-Synthesis** 子目录，与仿真的 ECE-Transfer 分开。

```bash
bash -c 'find "$HOME/tsclient" -maxdepth 6 -type f -path "*/ECE-Synthesis/ece_synth_menu.sh" -exec bash {} \; -quit'
```

脚本复制包到学校 `~/xzy01-synthesis/session-*` 再运行，避免在重定向共享文件夹中综合。库由学校原路径读取；实际读取前记录 SHA-256、文件大小及配置，库字节不回传。若共享目录断开，保留 school HOME 的 outbox，按终端打印的 `ship` 命令补传，仅复制结果，不再次综合。

此次新增综合包使用共享文件夹传输；已有 Git VCS/Xcelium 路线继续有效。新增综合入口的源码会同步到 GitHub，综合包/商业输出仍留在本机和共享目录，尚未加入原仿真 Git 结果分支协议。

## 命令行入口

```powershell
.\lab.ps1 synth template
.\lab.ps1 synth check
.\lab.ps1 synth list
.\lab.ps1 synth pack --run-dir runs\paired-a32 --job m01__real_overlap__s001__control --tool dc
.\lab.ps1 synth collect
.\lab.ps1 report
```

`template` 只在配置不存在时创建；已有文件请用窗口编辑。默认配置是 `config.local.synthesis.json`（Git 忽略），DC 和 Genus 分别保存 `libraries`、`corner`、`sdc_file`、`constraints_reviewed`、`timeout_seconds`。SDC 原字节会冻结进包，不自动推断时钟、复位、输入输出延迟或负载。

目前支持已有评测流程提取的单模块 RTL；任意“仅生成”结果尚无固定任务和审核后的源绑定，不能直接混入已有评测成绩。若 SDC 依赖其他文件，应先整理成可独立运行的一份约束；当前包不会自动收集外部 Tcl 依赖。

## 实际执行内容及状态

DC 使用 `analyze → elaborate → link → 读取 SDC → check_design → compile`，导出 Verilog 网表、DDC、输出 SDC、面积/时序/约束报告。Genus 使用 `read_hdl → elaborate → read_sdc → syn_generic → syn_map → syn_opt`，导出网表、SDC、面积/时序与未解析引用检查报告。

这些是新的适配模板，还需在学校对应版本、真实库和约束下验证。模板不启用物理综合，不作布局布线、功耗活动分析或签核；没有选择默认工艺库，也没有将 Yosys 的通用单元数换算成芯片面积。

| 状态 | 含义 |
|---|---|
| BLOCKED_PREREQUISITES | 缺库、角、审核后的 SDC 或运行环境；没有启动综合 |
| READY_FOR_SCHOOL_PREFLIGHT | 本机配置完整；学校库可读性、许可和实际命令仍待检查 |
| TOOL_FAILED / TIMEOUT / ENV_ERROR | 工具非零退出、超时或进程启动失败 |
| OUTPUT_INCOMPLETE | 退出码为零，但缺少要求的报告或网表 |
| COMPLETED_REVIEW_REQUIRED | 原始输入、执行记录、库指纹、完成标记和输出齐全；必须人工审阅 |

`COMPLETED_REVIEW_REQUIRED` 不自动计为“综合通过”、功能等价或时序达标。特别需要检查未解析单元、未约束路径、约束是否适用、库角/单位、时序违例；输出面积和延迟只在相同库与约束条件下可比。结果为用户回传的执行证据，不是远端主机可信认证。

结果目录：`workflow/synthesis/report.html`、`summary.csv`、`returned/`；每次尝试独立保存、去重导入。历史 Yosys、Icarus、VCS/Xcelium 成绩不改写。

## 参考来源

安装路径、版本和启动结论来自用户提供的 ECE_SYNTHESIS_STARTUP.md。模板命令组织另参考 [Cadence 社区的 Genus 综合示例及官方回复](https://community.cadence.com/cadence_technology_forums/f/digital-implementation/55520/genus-standard-cells-to-module)、[ETH Zurich 原始 DC 脚本](https://iis-people.ee.ethz.ch/~sha3/shabziger/synopsys/scripts/compile.tcl.html) 和 [MacroPlacement 项目自己的 Genus 流程说明](https://tilos-ai-institute.github.io/MacroPlacement/Flows/scripts/cadence/)。这些资料不替代学校安装版本的命令帮助及实际验收。
