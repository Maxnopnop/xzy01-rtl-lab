# 学校端36份RTL四工具操作

已准备144个独立工具任务：36×VCS/Xcelium/DC/Genus，包含本机失败。不是144个新模型样本。尚未在学校执行；本机27/36功能通过、35/36综合通过仅为旧记录，绝不覆盖。

共享映射用户已确认：Windows C:/Users/A/Documents/FYP ↔ 学校 $HOME/tsclient/FYP。本机已放置 main36-school-v1.zip、main36-school-stage-v1.sh、main36-school-commands.md；不需要再调用模型或提供Key。

## 1. 学校终端检查共享并导入HOME

```bash
timeout 30s ls -l "$HOME/tsclient/FYP/main36-school-v1.zip" "$HOME/tsclient/FYP/main36-school-stage-v1.sh"
printf "%s  %s\n" "865b7daf908ec0e57c1075f8e0b8e3ca719961fd9dc693a816055f578058b002" "$HOME/tsclient/FYP/main36-school-stage-v1.sh" | sha256sum -c - && bash "$HOME/tsclient/FYP/main36-school-stage-v1.sh"
```

出现HOME VERIFIED及READY_FOR_ONE_MANUAL_CASE再运行。脚本先校验ZIP/成员hash，复制到HOME，检查Python/tcsh/bash、四个setup、Nangate .db/.lib可读性；不获取许可证、不运行EDA。若BLOCKED/路径缺失/超时，保留输出并报告，不跳过校验。当前位置不限，bash与python命令可从原tcsh终端调用。

## 2. 手动单例仿真、综合

先从第001份RTL开始，每条等提示符返回再执行下一条：

```bash
python3 "$HOME/xzy01-main36-school-v1/school_main.py" run 001 vcs
python3 "$HOME/xzy01-main36-school-v1/school_main.py" run 001 xcelium
python3 "$HOME/xzy01-main36-school-v1/school_main.py" run 001 dc
python3 "$HOME/xzy01-main36-school-v1/school_main.py" run 001 genus
```

其余002—036的全部144条命令见[ALL_COMMANDS.md](ALL_COMMANDS.md)，共享根也有main36-school-commands.md。001—012为055，013—024为124，025—036为072；具体模型、RAG与样本映射逐条列出。不得只运行原PASS。

现有学校权限和脚本按“一工具一案例手动运行”；没有run-all、SSH调度或自动批处理入口。不要整块粘贴144条命令绕过出错检查。每工具最多600秒；不得重跑已有案例。环境/许可证/超时/未知异常先停下报告。功能FAIL保留；CHECK_COUNT_DIFFERENT保留实际计数，不改期望凑PASS。综合COMPLETED_REVIEW_REQUIRED仅表示产物返回，仍需审阅日志，不代表逻辑等价或时序签核。

工程约束单独保存：055/072组合最大输入输出延时10库时间单位；124为clk正沿、10单位时钟、零外部IO延时。原题未给频率；约束是本轮工具可综合性smoke，不是原题新增条件或正式PPA指标。沿用已核过的Nangate typical路径，但现场库hash、工具版本及许可仍须核对。没有自动门级仿真或形式等价。

## 3. 学校进度与仅补传

```bash
python3 "$HOME/xzy01-main36-school-v1/school_main.py" status
```

执行结果保留于 $HOME/xzy01-console-single/console-<key>，完成后自动平铺回传return-console-<key>.zip/.json到共享根。若仅回传失败，保留HOME结果并只补传（例001的VCS）：

```bash
python3 "$HOME/xzy01-main36-school-v1/school_main.py" ship 001 vcs
```

ship可换对应编号/工具，绝不启动EDA。已有相同内容可补传，异内容拒绝覆盖。UNKNOWN_OR_RUNNING或manual-one.lock表示可能尚在执行或曾中断，不能自行删目录、删锁重跑。

## 4. Windows CMD回收并验证

每完成一些或全部工具后可执行（仅校验/导入，不运行EDA）：

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch\exploration\20261029\main36-school-v1\Collect-Results.ps1"
```

报告另存在collections/collection-时间.json。VERIFIED表示通过回传来源/输入hash/日志校验，不表示工具结果一定PASS；RETURN_NOT_FOUND为尚未回传，IMPORT_REJECTED需保留并排查。综合原始netlist/SDC/面积/时序报告返回，原DDC等未列入已审回传白名单的额外文件留学校HOME，不在本次ZIP内。回收全部36分母及失败，不替换或修补RTL。

## 离线检查与保全

453项检查通过：144 ZIP/原DUT、仿真TB/参考/检查数、综合SDC匹配、安全HOME暂存、已有更改拒绝覆盖、Python3.6兼容、一次只运行一个案例、防重、模拟仿真/综合回传及篡改拒绝。Bash语法和PowerShell入口检查通过。模拟回传只在offline目录，不是学校结果。学校实际环境当前未知。

source-results-lock.json绑定原36响应/输入/RTL/结果与本机日志；所有原证据保留。新兼容console manifest仅为学校导出，未发模型release、不授权生成。旧UNKNOWN/403及旧学校211/212对213计数差异仍保留。本轮0模型、0学校EDA调用。
