# 控制台多模型 v3 离线交付（待总控审核）

结果：独立 v3 实现完成，离线验收通过。没有模型生成/embedding调用，没有学校工具调用，没有创建任何真实实验 release。旧 v2 的22项测试仅作为兼容回归；本轮新增31项。

## 代码与入口

- 仓库根：console_bridge_v3.py、console_catalog_v3.py、console_cli_v3.py、console_gui_v3.py、console_school_v3.py、console_school_runner_v3.py、console_stage_v3.py，Open-Lab-v3.cmd/.ps1。
- 协议与限制：../../CONSOLE_MULTIMODEL_V3.md。
- 唯一新版源码锁：本目录 delivery-source-lock.json（相对仓库根）。evidence-lock.json 为本目录证据锁。v2 的有效锁 delivery-final/delivery-source-lock.json 保持不变，不把旧锁冒充新版锁。
- 新账本使用本目录 dispatch/、slot-reservations/、school/、school-returned/；本轮未建立真实推理预约。

## 验收矩阵

| 项目 | 证据与结论 |
|---|---|
| 动态模型数 | 1/2/3/5模型、两臂、各2样本，冻结数量/编号/顺序/调用上限验证；31项新增测试内覆盖 |
| 三开发商 | OpenAI、Anthropic Claude、DeepSeek exact IDs；模型作者与 OpenRouter provider tag/name 解耦 |
| 请求不改写 | 三开发商逐槽原始请求字节传给 mock；真实 loopback HTTP 三请求逐字比较；消息原文件与 retrieved bytes 分组严格一致 |
| 兼容参数 | 不支持字段、未知控制、声明值变化、未审核模型差异、calls_only token键含null拒绝；不注入8192 |
| 失败边界 | 未知模型、空端点、metadata hash变化、模型/provider漂移、HTTP错误、超时、密钥回显、无release、重复槽/跨包重复/跳槽均拒绝或STOP；无重试 |
| 学校四工具 | 实际生成4个独立ZIP/launcher/校验/补传脚本，Python3.6语法解析；4种mock执行→平铺return→控制台导入通过；未知/已运行目录不重跑 |
| HOME staging | integrity-and-wsl-stage.json：四份实际ZIP在WSL临时HOME复制、SHA核验、安全解包成功，全部0退出；未启动任何工具 |
| 回收语义 | VCS mock212、Xcelium mock211对213保留CHECK_COUNT_DIFFERENT；DC/Genus mock保留COMPLETED_REVIEW_REQUIRED，未称功能/时序通过 |
| GUI/CLI | 隐藏Tk真实实例读取336条历史及动态模型包；终端脚本manifest/release hash绑定；PowerShell两入口解析0错误，未运行生成入口 |
| 新旧总回归 | tests-final.txt：31项v3 + 22项v2 = **53/53通过**，16.148秒 |
| 原runner | regression.txt：**24项，22通过、2跳过**，71.646秒；两项需Windows原生Yosys，本轮未伪称通过 |
| 保护证据 | preservation-final.json：旧v2/学校159文件和原历史6320文件逐项比较；须changes为空才生成锁 |

## 具体可审阅示例

examples/model-packet/console-package.json 为6槽三模型离线示例，包含真实公开端点快照；不是实验选题/RAG包。purpose=OFFLINE_FIXTURE，代码禁止其放行。

examples/Start-One-NOT-RELEASED.ps1 为实际导出的终端入口，绑定 examples/NOT_RELEASED.json，不含密钥。不能拿示例作为真实调用放行。

examples/shared-root/ 为实际4份单案例ZIP与stage脚本；examples/{dc,genus,vcs,xcelium}-record.json 记录原清单、ZIP与脚本哈希；同名 -commands.txt 保存校验/人工单次/仅补传命令。examples/Import-Flat-Return.py 为平铺回收入口，examples/example-file-hashes.json 给出每份示例文件SHA。

学校示例使用历史slot25的原RTL/TB/reference做传输模板，未修改原文件；综合配置明确使用不存在的 SYNTHETIC_NOT_FOR_EXECUTION 路径，不能用于真实学校运行。没有新增网表门级仿真或形式等价。

## 公开元数据

catalogue/保留5次未认证GET的原始JSON、source URL、UTC与SHA：总目录、OpenAI4.1-mini端点、Claude4空端点、DeepSeek-chat-v3.1端点、Claude4.5端点。全部无推理请求。

示例选路分别为 openai / OpenAI、anthropic / Anthropic、deepinfra/fp4 / DeepInfra。Claude4端点为空是保留的限制；另建Claude4.5离线样例不是替换任何已冻结实验模型。

官方文档依据：https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model ，https://openrouter.ai/docs/guides/routing/provider-selection 。目录可见不证明账户实时可调用；没有付费探测。

## 未验证与审核阻断

真实账户推理、学校现场新版脚本均未验证；不能据mock评价RTL能力或PPA。标准响应只有provider显示名，不能证明同名服务商内部具体端点/地域未变化；结果明确记录该界限。supported_parameters不能保证所有参数值/组合有效，真实拒绝会停止而不改写。token/cache/reasoning/cost口径和服务默认输出限制需科学比较审阅。

学校命令默认映射为$HOME/tsclient/FYP，其他映射需明确配置路径；附加assets学校打包目前拒绝。Git传输没有实施。旧冻结v1执行包继续v2入口，新版不迁移旧已预约槽。

本交付只供总控审核，再由探索准备真实schema v3包、参数差异说明及来源锁。用户/总控正式审阅与执行release仍必需；本轮不能据通过测试直接开始API实验。
