# 新完整36次脚本包：待总控独立审核

用户2026-10-29明确同意保留旧首槽UNKNOWN、预约和STOP，另建完整36次，累计最多37机会。原35槽接续方案取消，未实现/未启动；旧35槽不放行，新36不能视为原失败补回。本包仅准备，0模型、0网络请求、0学校/本机EDA执行（工具发现与hash读取不计EDA）。

## 范围与字节

3题055/124/072，openai/gpt-4o-mini、openai/gpt-4.1-mini、openai/gpt-5.6-luna，有无RAG×2样本=36。新ID rag36b1-001..036，batch.json每槽含parent_slot_id与原request_sha256，完整36请求/原题/TB/ref/48段RAG/messages保持原字节。复制的inputs包含原归档文件供保全，但batch只有36条，不能执行300草案。旧原包874文件及事故父证据未变。

调用预算calls_only，无token/美元硬上限；累计旧1UNKNOWN+新36=最多37。旧费用未知，新的已报费用之和也不能冒充完整账单。原模型参数与语义限制不变：Luna medium、另两模型默认，非等计算量；参考同源不是独立oracle，公开训练暴露未知，3题探索性；旧代理回归失败和学校211/212对213差异均保留。

## 运行入口和停止规则

Start-Experiments.ps1默认Status，-Action Preflight需新release且不需要密钥；-Action Run先离线预检，再一次Read-Host -AsSecureString，随后顺序最多36，不每槽确认。不恢复自动化，不后台自动启动。运行结束移除新密钥或恢复原进程环境值。调用主机返回状态逐槽打印，runner.py status只读显示总账。

gate不接受旧CONSOLE_EXECUTION_RELEASE。需要总控另发NEW36_SCRIPT_EXECUTION_RELEASE，字段见release-fields.example.json（故意NOT_RELEASED_EXAMPLE/user_approved=false，不能运行）。新release绑定source-lock-r2、batch、parent-evidence-lock、offline-audit-r2、全部36新ID、短运行根及累计37预算。

runtime为本目录live/jobs/001..036；实际路径探针覆盖响应、原始输出、编译/仿真/Yosys输入输出等756个路径，最大长度见final-audit。超长根在mkdir前拒绝；主响应文件在任何预约/发送前打开，避免发送后才发现路径不能打开。探针读写后只移除本次探针，不删除任何执行证据；live当前仅空目录。

单进程exclusive.lock与RUN_STARTED写前持久化。每槽先全局独占预约（与v3共用slot-reservations）及本地预约、fsync，再单POST。新ID不可跨入口重复；旧父证据变化或旧批后35出现预约会阻断。任何再次启动均拒绝自动接续，即使此前完成正常；用户需审核状态，不得删lock/RUN_STARTED/STOP绕过。崩溃保留锁或预约，UNKNOWN不重发。成功响应保留完整transport回执；主保存失败尝试另存receipt-write-error，始终停止，磁盘完全失效时仍靠预约阻断。

普通FUNCTION_FAIL、COMPILE_ERROR及SYNTH_FAIL保留并可继续。CHECK_COUNT_DIFFERENT、超时、工具环境失败、服务错误（含403）、未知、model/provider不符、提取失败或其他后处理异常停止。源码/父锁每槽发送前重核。不补样、不换模型、不切换provider/fallback。

## 路由与依赖

复用原已审transport.py字节，SHA7ba1d3b47e2e471a9f11d226c65700d3cd70535b581fe7863a4fa4ed27c98524，仍固定OpenRouter chat/completions、provider only openai、fallback=false。proxy_url=None明确沿用当前已冻结36槽控制台路由，不沿用更早实验的explicit_local，也不读取ambient代理；未做真实网络可用性探针。若网络失败停止，不能静默改代理。

reuse/console_bridge_v3.py、console_catalog_v3.py、rtl_lab.py以及声明的ece_synth_common.py/ece_synth_school.py均为原文件快照，绑定新source-lock-r2；公共源码不改。生产脚本只调用bridge.extract/local_replay，不调用bridge.dispatch/transport/gate。local_replay通过快照ROOT取依赖锁、动态导入同一reuse/rtl_lab.py；该路径已在离线测试断言，完整三阶段命令用mock进程驱动。rtl_lab被用到的进程函数只依赖Python标准库；复制了全部declared dependency文件，学校模块未执行。Python/Icarus可执行文件与Ubuntu /usr/bin/yosys哈希见tool-discovery.json，启动重核；不宣称整个操作系统/动态库可复现。真实新模型输出下EDA未测试。

## 离线证据及负结果

offline-audit-r2.json：24项通过，包括36全程逐字节/全局预约、功能失败继续、编译失败继续、检查数差异停止、403零重试、UNKNOWN停止、身份/截断/提取错误、键盘中断、真实os._exit崩溃、独占锁、跨入口防重、发送前打开失败、发送后保存失败、结果保存失败、超长路径拒绝、源锁漂移和旧release拒绝。网络socket被拦截，模型回执纯本地注入，judge是mock；真实local_replay单独使用mock run_process验证导入/深路径/参数，未重跑参考。

首轮21项有1 ERROR：超长负例在mkdir时先抛FileNotFoundError，而测试期望ValueError；原日志/offline-audit与源码保存在development-r1，原offline目录不删。修订为mkdir前路径限长，第二轮通过。PowerShell首轮测试计数器用了错误script作用域，序列日志已表明preflight无key、run有key；原ps-offline trace和测试源码保留。第二轮改测试计数器作用域，powershell-audit.json证实实际PS5.1入口一次隐藏提示且清理密钥。未改生产入口来迎合测试。

## 用户命令

在CMD先查看状态（0模型）：

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch\exploration\20261029\main36-script-newbatch-v1\Start-Experiments.ps1" -Action Status
```

正式Run需待总控出新release后提供其真实路径，不把示例、旧release或占位路径交用户执行。当前不具备启动放行。总控可在独立临时目录重放测试（测试目录固定且独占，需要独立副本或调整测试输出根），不得在原离线证据目录覆盖重跑。
