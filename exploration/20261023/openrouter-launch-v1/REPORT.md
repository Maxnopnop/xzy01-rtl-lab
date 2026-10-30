# OpenRouter 路由与前三槽启动准备

状态：PREPARED_NOT_RELEASED。新包不改 direct-api-v1 已封存文件，不创建 technical-release，不生成。

## 目录与路由
本次新增3次无密钥公开目录GET，各一次，无重试，无生成；原响应和SHA在三份 *-endpoints.json 与 catalog-receipts.json。先前总控GET未存原HTTP，不能把这次读取冒称原响应。官方路由依据见 routing-basis.md。
最终固定 route.json：普通 openai / OpenAI，显式HTTP CONNECT代理127.0.0.1:3213。三目录各仅一项普通OpenAI，另外fast/flex为需显式选择服务层。无service_tier字段，不增加费用更高的fast参数。早期azure/us仅候选，未执行。
三端点context_length=1050000，40份messages序列化最大4347 UTF-8字节；未精确计token。请求未启用plugins/transforms；官方默认压缩仅<=8192上下文端点，当前不满足。公开规则支持不触发该默认压缩，但不证明账户或服务内部无不可观察处理。provider返回名尚待原正式槽核验，不能证明具体机器、模型权重或内部零重试。

## 离线核验及保全
audit.json：240请求的messages与冻结原文一致；40组内跨模型/样本去除model后请求相同；原包1963、缓存修复280、原all20 752、旧executor1928文件全部匹配。没有重跑旧27矩阵/120HTTP捕获。
launch.py门禁7个断言覆盖缺放行、绑定错误、顺序/范围变化、材料漂移及合法夹具。测试仅临时文件，不签实际放行。
powershell-tests.json：12组合覆盖原变量不存在/空/有值、Preflight/Run、成功/失败；只调用本地伪Python，不调用真实传输。初版失败保留：当前.NET把null环境设置成空值，原来不存在会留下空变量；新版显式记住存在性并在finally恢复/删除，12组合通过。初版代码及失败另存，不掩盖。
项目规定的默认 unittest 回归单列 default-regression.txt/exit.txt，失败按原样保留，不修改旧成绩。它不是旧HTTP矩阵或正式模型实验。
本次默认回归：24 tests / 3 failures / 1 error / 2 skipped，exit 1，耗时74.458秒；不修复全局runner，不重试。与历史失败计数一致不代表每个根因已独立重审；完整trace保留供总控判断。

## 总控审核与入口
launch-lock.json绑定入口/配置/证据；总控除原source/input/route绑定外，须在 direct-api-v1/runtime/technical-release.json 加 launch_lock_sha256 并保持 permitted_ordinals=[1,2,3]。launch.py仅接受该前三槽，原dispatcher仍独立预检且每槽再检，原账本复用，不复制运行目录。review-bindings.json列具体hash供复核，不是放行文件。
前三槽准确为同一首题、no_rag：Luna样本1、Luna样本2、Terra样本1。不是三模型各一次；计入原240，不增接入探针。

用户在独立PowerShell终端安全输入key：
```powershell
& 'E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261023/openrouter-launch-v1/Start-FirstThree.ps1' -Action Preflight
```
此入口先只读预检，未签放行会阻止。总控绑定审核通过并通知用户后才使用：
```powershell
& 'E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261023/openrouter-launch-v1/Start-FirstThree.ps1' -Action Run
```
Run也先预检，仅成功后进入同一旧dispatcher；无自动重试、补样、续写或扩批。失败停止并保留账本。key不写参数/文件，只临时进程环境，finally恢复原存在性与值；硬杀进程时该终端进程内key随进程结束，不写用户/系统环境。脚本默认Preflight，不应在聊天粘贴key。
真实usage缺失为null，网关内部重试不可观察，原180秒请求、12000秒执行墙时等保护继续。该封包只提供准备证据，不授予执行权限。
