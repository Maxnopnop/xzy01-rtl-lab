# 共享子目录不可见时：固定包复制到学校HOME

2026-10-24用户返回check状态BLOCKED，46条PACKAGE错误覆盖四个子目录，model_calls/tool_calls均0。原校验把缺失和hash不符合并为PACKAGE，具体远程文件系统原因尚未确认；Windows端48原文件哈希均正确。改用一个ZIP传输至HOME，不改任何原实验文件或工具入口。新run-local.py只负责本地手动调度一个工具及平铺回传。

## 学校端

先刷新共享根目录，再运行准备脚本：

```bash
timeout 30s ls "$HOME/tsclient/FYP"
bash "$HOME/tsclient/FYP/verify25_stage.sh"
```

该脚本复制单个ZIP到$HOME/xzy01-console-transfer-v1，检查ZIP SHA、51个成员（48原文件+3传输元数据/入口）、原文件SHA及学校依赖。仅检查，0工具。复制超时/哈希不符时停下报告，不跳过。ZIP SHA256：238288af017b6d7a5e405e60873c17d2c27c56f38d055e932b233536e8f16d91。

出现READY_FOR_FOUR_MANUAL_COMMANDS后，逐条运行，等上一条返回提示符：

```bash
python3 "$HOME/xzy01-console-transfer-v1/run-local.py" run vcs
python3 "$HOME/xzy01-console-transfer-v1/run-local.py" run xcelium
python3 "$HOME/xzy01-console-transfer-v1/run-local.py" run dc
python3 "$HOME/xzy01-console-transfer-v1/run-local.py" run genus
```

所有工具读学校HOME文件，不从tsclient读源码。保留同一四包ID和防重复目录；已执行过的包拒绝再次run。CHECK_COUNT_DIFFERENT保留，可继续另一预定独立工具；环境/许可证/超时错误先停下报告。结果保存在学校HOME，并复制到FYP根目录的return-console-<id>.json/.zip。成功平铺传输显示FLAT RETURN COPIED。

只补传一个已完成结果，不执行工具：

```bash
python3 "$HOME/xzy01-console-transfer-v1/run-local.py" ship vcs
```

工具名可换为xcelium/dc/genus。与已有不同回传拒绝覆盖。

## Windows回收

```powershell
& 'E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch\validation\console-school-four-slot025-v1\Import-Flat-Returns.ps1'
```

校验平铺回传key、原manifest及ZIP SHA后复制到对应控制台inbox，再调用原console_school.collect进行白名单、输入hash及日志验收。没有EDA/API调用。完成后控制台仍可载入records中四个记录，用“回收结果并验hash”查看。当前旧“复制命令”按钮仍是共享直接运行入口，本次用本文HOME命令。

离线验证：WSL真实解包48原文件全部一致，学校依赖在WSL缺失被正常拒绝，0EDA；平铺回传与重复同内容补传通过，异内容拒绝；回收复制和篡改拒绝通过。现场执行/返回仍待用户完成。
