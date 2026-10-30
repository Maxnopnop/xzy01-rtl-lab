# 控制台 v3：多模型冻结包与 HOME 单案例

独立入口 `Open-Lab-v3.cmd`（GUI）、`console_cli_v3.py`（终端）。打开/导入/预览不调用 API。本版本不构成实验放行；本轮仅公开元数据 GET、离线 mock、WSL 暂存、回归。旧 v2 文件及其有效锁不变；旧96/240仍只读显示。旧 console-frozen-v1 包继续使用 v2，新版只执行 console-frozen-v3。

## 冻结包契约

探索负责准备真实包，控制台不选题、不改题、不拼接/重写 prompt、不修改 RAG。示例在 `validation/console-multimodel-20261024-v1/examples/model-packet`，全部为 OFFLINE_FIXTURE，不能放行。

- `schema=console-frozen-v3`；`models` 是明确的非空模型列表，数量由包决定。每项包含 `id`、`author_namespace`、`provider_tag`、`response_provider`、`parameters`、`comparison_note`、`endpoint_metadata`、`metadata_source`。没有模型别名、默认替换或固定三模型白名单。
- 端点 JSON 与 source JSON 都进入 `files` SHA256 清单。source 包含精确公开 GET URL、UTC 时间、原始响应 SHA、authenticated=false。端点的 `data.id`、`tag`、`provider_name`、status=0 与声明一致。请求参数必须同时在控制台支持集合和所选端点 supported_parameters 中。未知/不支持字段直接拒绝，不静默删除；参数值与声明逐项一致。
- 每个 slot 包含 id/ordinal/task/condition/model/sample/request/spec/testbench/reference/top/expected_checks，及 `messages_file`、`retrieved_file`，所有文件锁定。实际请求 messages 必须等于冻结消息；同题同条件所有模型/样本的完整消息文件和检索片段文件逐字相同。同题原 spec/TB/reference/assets/top/固定检查数相同。控制台不证明片段的科学来源与选题隔离，这仍由探索包及总控审阅负责。
- 每题恰有 no_rag/rag 两臂，每臂覆盖完整声明模型集合、相同样本编号/次数。ordinal 为连续有限顺序；max_calls 等于全部槽数。`calls_only` 不允许任何输出 token 上限键（包括 null）；不注入8192。另一个明确协议 `calls_and_output_cap` 允许冻结正整数上限，但不自动选用。
- 完整 request.json 原字节一次发送，provider 为唯一声明 tag，allow_fallbacks=false，require_parameters=true。禁止 models/fallback/streaming/tool 字段。未知结果、HTTP错误、身份不匹配、提取/基础设施异常保留证据并 STOP，不重发、不换模型、不补样、不扩批。

## 元数据与路由界限

公开目录获取命令：`console_catalog_v3.py --model author/exact-model --output 新目录`；不传 model 获取总目录。只做一次未认证 GET，不做推理/embedding/余额检查，不自动重试。目录可见不能证明账户权限、额度、即时容量或真实推理可用。

本次示例：openai/gpt-4.1-mini → openai / OpenAI；anthropic/claude-sonnet-4.5 → anthropic / Anthropic；deepseek/deepseek-chat-v3.1 → deepinfra/fp4 / DeepInfra。这些是离线适配样例，不是本次实验指定名单。claude-sonnet-4 返回空 endpoints，保留原记录并视为不可导入端点，不自动换4.5。

作者 namespace 与上游服务商分开。请求冻结端点 tag；标准返回只提供 provider 显示名，能拒绝已观察到的 provider/model 漂移，但无法证实未暴露的同名服务商内部端点/地域/精度没有改变。结果明确记录此限制，不能称为完整路由或服务端隐藏包装证明。官方依据：https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model 和 https://openrouter.ai/docs/guides/routing/provider-selection 。

采样/推理参数可以在不同模型间明确不同，但必须写 comparison_note、冻结全部 profile 并由总控另行审阅；控制台不声称这些设置科学等价。supported_parameters 是字段能力声明，不保证每个参数值/组合都被当前账户接受；未接受的真实请求仍停止，不自适应修改。usage/cost 原样保留，未报告为 null，包含原始 cache/reasoning 字段，不按服务商猜测/统一计价。无显式 cap 不表示服务端没有默认输出限制。

## 执行关卡与账本

新版状态位于 `validation/console-multimodel-20261024-v1/dispatch/<manifest hash>`；槽位全局预约目录独立。预留先于 POST；失败/unknown 不返还槽；跨包同 ID、历史96/240和 v2 已预约 ID 均拒绝。沿用已审单 POST transport hash；无自动重试、重定向跟随或外部调度。

真实包需要单独的总控 release，含 v2 同类 owner/reviewer/manifest/source/transport/max_calls/ordered permitted_slots/budget/180秒/0重试绑定，新增 `model_profiles_sha256`（canonical UTF-8 sorted JSON）和 `model_comparison_reviewed=true`。`source_hashes` 为 `console_bridge_v3.bridge_bindings()` 返回值；`bridge_sha256` 指新版 bridge。控制台不生成放行。示例 NOT_RELEASED.json 与 OFFLINE_FIXTURE 双重阻止实际运行。

GUI导入后显示完整模型 profile，所选槽详情保留参数与 usage。密钥隐藏输入仅当前进程内存，终端 getpass；导出的 PS1 绑定 manifest/release hash，不含密钥。

## 学校 HOME 传输

GUI为一个已存原 RTL 选择一个工具打包；VCS/Xcelium沿用原测试，DC/Genus必须提供已审核库配置/SDC。库只保存路径，不打包库。附加 assets 目前明确拒绝，不能静默丢弃。

1. 选择 Windows 映射共享根目录，输出 `console-<id>.zip` 和 `stage-console-<id>.sh` 两个平铺文件。脚本/ZIP/清单/逐文件 hash 全部绑定。
2. “仅检查共享命令”复制到学校终端，验证 stage 脚本 hash，限时复制 ZIP 到 HOME，再验证 ZIP 和每个成员。安全白名单解包到 `$HOME/xzy01-console-v3/<id>`，不启动 EDA。已有不同内容拒绝覆盖。
3. “复制命令”产生 stage 校验后仅该包一个工具的人工启动命令。运行器拒绝共享目录直跑；单次工作目录独占，unknown 不能重跑。没有四工具批处理命令、SSH或自动学校调用。
4. 结果保留 HOME，并平铺复制为共享根 `return-console-<id>.zip/.json`。仅补传命令不执行工具，同内容重复补传允许、不同内容拒绝覆盖。
5. GUI选择对应记录与平铺 sidecar，校验 ZIP SHA/key/manifest/原输入/白名单/日志后导入新版 ledger。另提供示例 `Import-Flat-Return.py --record ... --sidecar ...`。

生成命令假设共享名为 `$HOME/tsclient/FYP`；学校映射名不同须在执行前明确替换该路径，不能从未知共享位置自动寻找并执行。目录枚举/共享传输仍依赖 Horizon；本轮 WSL实际验证了 ZIP→HOME，未重跑学校现场。未来 Git 方案未实施。

VCS212、Xcelium211 对原预期213仍是 CHECK_COUNT_DIFFERENT；DC/Genus产物收齐仍 COMPLETED_REVIEW_REQUIRED。不会自动做新网表门级仿真、等价验证或签核。历史四工具证据只读展示。

## 验收入口

本轮验收、元数据、示例和最终源码锁见 `validation/console-multimodel-20261024-v1/ACCEPTANCE.md`。真实模型可用性与新版学校现场运行均未验证，不能用旧 v2 的22项测试代替本轮验证。下一步仅总控审阅交付，不要求用户先消费 API 验收。
