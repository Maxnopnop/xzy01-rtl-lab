# 新8题96槽执行器：技术审核材料

状态：OFFLINE_READY_PENDING_COORDINATOR_TECHNICAL_RELEASE。用户已批准8题96槽，无需再问实验意图；本次真实模型请求0、真实密钥读取0、生产预约0。只在本新目录新增执行器与离线证据，原题/参考/test/RAG/prompt及旧批不变。

## 输入与新运行边界
唯一输入为兄弟目录 public-rag-next-v1 的封存254文件包（packet SHA a8f24bd42a5b3d6bf3b4a7f12732dc9aa6f601347862f5538be61243677fecee）。直接从 C/requests 读取原文件bytes，哈希核对后逐字写入工作目录发送；没有重建messages、附加system或模型专用说明。96捕获逐字相同。
三请求模型准确为openai/gpt-5.6-luna、terra、sol；provider.only=openai、allow_fallbacks=false、require_parameters=true；精确响应model/provider核对。route.json与输入包原route字节一致，显式127.0.0.1:3213代理。transport.py与已审版本逐字相同；usage_record函数AST相同，只移除旧未使用8192payload适配函数。
新runner/ledger仅使用新96槽；不导入旧dispatcher、旧20题映射、旧240账本/STOP/预约/放行。唯一正式目录是本包runtime/live-run（本次未创建），不存在命令行另选run路径。旧失败83/197不重发、不映射。

## 预算、停止与执行控制差异
96总机会，并发1，无8192输出token硬cap，无整批墙时cap。单HTTP请求180秒，继承worker硬守卫180.5秒（清理开销另记）；编译15秒/仿真10秒。HTTP响应1MiB，模型文本128KiB，stdout或stderr各2MiB，单job8MiB，全run512MiB；新job启动前预留8MiB余量，过程中/后续再次检查。未购买或改账户配置。
reserve/fsync在发送前完成。未知、首次服务/协议/资源错误立即STOP；不自动retry/fallback/续写/补样/接续。持久化未完预约不重发；即使失败result.stop已落盘而STOP尚未写入发生崩溃，recover也补写STOP并阻止下一槽。已有exclusive.lock不自动删除或接管。
普通RTL拒绝/提取失败/编译失败属于模型结果，按原规则保留，不按质量补样；编译/仿真超时、原TB的TIMEOUT、文本超128KiB均为停止事件。HTTP200内嵌error亦停止。相对旧core新增这些资源/服务停止处理，不改输入或评分逻辑。
raw usage保留，缺失字段null，reasoning不重复加到output；汇总仅对已报告字段求和，逐项列缺失数。usage.cost只汇总服务明确报告的非负有限数，不凭定价推算；不把部分合计当完整账单。

## 原参考工具兼容校准
预冻结calibration-plan及8份隔离夹具，唯一改动是复制参考中的模块名RefModule→TopModule。原ref/test文件逐字复制到工作目录同时编译。
实际8 compile +8 simulate，均rc0、0差异，共32047个原TB采样；各题20/100/213/224/1041/210/219/30020。无异常重试，无新增诊断向量。证据 calibration/summary.json、逐phase日志及evidence-lock.json。
这是同源参考别名自比较，仅说明当前工具/包装兼容。REFERENCE_PASS不是独立规格正确性。原TB active-edge评分、X屏蔽、094明确dont-care、143缺multi-hot覆盖，以及019/087和114/106相关题组继续保留。正式结果存条件标签与history_relation，不改旧标签。

## 有限离线测试
- mock/summary.json：31检查全通过，104个loopback POST（96原bytes成功夹具+8服务故障），0外部API。96槽完成后重复启动没有额外POST，第97预约拒绝。
- 400/403/429/502/HTTP200内嵌502/307/断流/超时：每场景只发1次，下一槽未启动，重启0新增send。307目标0POST。mock响应使用OpenAI字符串仅为夹具，不是实测provider权限。
- 未完预约→UNKNOWN不重发、已有stop:true但无STOP→阻断、哈希漂移/锁占用/磁盘资源阻断；128KiB边界、超限、双代码块、危险RTL、模拟timeout/TB TIMEOUT及正常编译错误分支均按声明处理。资源/判题分支使用本地假process，不额外启动EDA。
- gate-tests/summary.json：12项通过。含合成放行、缺/错放行、空key、96范围、输入/source/route/hash、重复身份与已存完整response未处理的恢复。合成放行仅在gate-tests/synthetic-release，生产runtime未创建。
- powershell-tests.json：PowerShell7 12组合通过（不存在/空/有值、Preflight/Run、成功/失败）；powershell51-tests.json：用户实际Windows PowerShell5.1 8组合通过（不存在/有值）。均假Python与合成key，不读取账户。
- 实际只读preflight当前ready=false，缺正式技术放行，credential_present=false，network_requests=0。这是预期封闭状态。

校准后仅ledger.recover的STOP恢复与runner的空key判据修改；初版代码/校准时source-lock保存在development，core/judge/工具/输入未变，无额外校准。最终source-lock覆盖修订版，mock完整针对最终版。静态发现与修复记录保留，没有抹去初版。
未重跑旧HTTP矩阵或legacy全仓回归；后者历史24tests/3fail/1error/2skip保留。本轮明确8+8校准限额，未为全仓回归额外启动EDA。新有限检查通过不等于全仓全绿。

## 总控放行与用户入口
review-bindings.json列具体source/input/route/calibration/mock摘要哈希；总控独立审查后在本目录runtime/technical-release.json创建正式放行（仅此路径）。technical-release.example.json是NOT_RELEASED模板，不能自行改名当审核。范围必须完整原1..96；首错即停，不自动另建续段。
用户在自己的PowerShell终端执行，key通过Read-Host -AsSecureString输入，不写参数/文件/聊天，结束finally恢复原进程环境存在性及值。默认Preflight只读不联网；Run同样先预检，通过后调用runner：

```powershell
& 'E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261024/public-rag-next-executor-v1/Start-Experiments.ps1' -Action Run
```

本条命令仅在总控签正式技术放行后使用。本准备者没有真实调用，也不会另启批次。服务端内部重试/提示变换仍不可由本地无重试证明；沿用已审路线的可观测边界。
