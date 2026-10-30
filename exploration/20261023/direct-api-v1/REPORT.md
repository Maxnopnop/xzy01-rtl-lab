# OpenRouter直接API适配：本地审计完成，尚未放行

## 结果

新direct-api-v1客户端真实loopback HTTP审计通过。27槽（3准确模型×400/401/403/429/超时/响应中断/redirect/成功/usage缺失）每槽仅1个实际POST；每槽再次进入账本均0新增POST。40题条件组×3=120份实际捕获请求，单列顶层model后其余JSON完全相同，角色/正文均与冻结messages一致。无CLI、无技能/环境/额外system提示、无模型别名fallback。这里比较的是客户端发送给网关的内容，不能证明网关/上游内部未加工。

总计本地148 POST=27矩阵+120完整输入+1显式代理验证；另1本地HTTPS CONNECT被mock407拒绝，确认CONNECT路径不携模型Authorization且未重试。没有真实API生成、真实模型、正式预约、EDA或默认回归执行。原有失败/成绩不动。

## 客户端与代理

transport.py用标准库http.client单次request，无SDK、redirect handler、auth challenge重试、WebSocket或fallback。非2xx停止，redirect不跟随，超时/不完整响应为UNKNOWN。没有以请求prompt限制token；9000输出token的成功fixture验证8192逻辑已移除。usage缺失保留原始None与各字段unknown；只汇总已报告用量，不把未知补0，不重复加reasoning到output。

代理必须由route.proxy_url或显式proxy_env选择；两者均null即明确直连。route值经校验后进入worker route.json，独立于core.clean_env。测试通过把origin设为未监听端口、proxy设loopback接收器，实证子进程实际走代理。HTTPS经HTTP CONNECT代理采用默认TLS证书验证；禁止嵌入代理凭据，不隐式继承全局代理。HTTPS代理URL/SOCKS本版本不支持并会拒绝。外部代理/网关自行重试不可由此证明。

## OpenRouter封装与目录状态

endpoint固定https://openrouter.ai/api/v1/chat/completions，credential env为OPENROUTER_API_KEY。原240修订requests仍只含原裸model/messages/stream；传输时精确映射为用户指定候选openai/gpt-5.6-luna/terra/sol，加入provider.only（共同单个经审核slug）、allow_fallbacks=false、require_parameters=true。没有models候选数组、:auto或替换模型。

最新总控元数据回执validation/openrouter-setup-v1/receipts/check-20261023T113443188105Z.json确认三个精确ID目录可见和key认证，generation_calls=0。目录/认证不证明推理、账单权限或实际权重身份。mock用mock-only与MockProvider，仅为夹具，不是假冒已找到真实上游。真实provider.only和响应provider名字目前留空，正式预检阻止调用。

OpenRouter provider slug可能覆盖端点变体；总控需审核上游目录后固定具体限制。allow_fallbacks=false是请求约束，不等于服务内部绝无重试。新客户端严格检查返回model及经审核expected_provider；不匹配即停，不别名修复。不支持/无权限只能在总控放行后的正式槽逐次观察，不能另加试调用冒充准备。

## 账本与放行

保留原240机会/原序/单并发；首段建议原前三槽，仍属于240。durable reservation在POST前fsync；已预约未知恢复不重发，锁阻止并发，源/路由/input变动不能复用同一run。runtime/live-run路径固定，不提供命令行重置新账本入口。请求SHA绑定具体wire bytes，并保留240修订源SHA。

180秒请求上限、8MiB/job、512MiB/run保护保留；当前沿用旧执行器更保守的12000秒整个run墙时停止（不放宽原28800秒总上限）。不自动续写、补样、重试、扩批。source-lock/input-lock/route及元数据证据须由总控签技术放行；例子decision=NOT_RELEASED，未创建真实technical-release。preflight只读本地，网络0。模型权限字段始终UNVERIFIED_UNTIL_FORMAL_RETURN，不要求伪签权限已证。

## 证据与验证范围

- mock-v1/predeclared-plan.json：预声明有限矩阵；summary.json全通过。
- mock-v1/captured/：148份原始HTTP请求体；http-observation.json保存计数/实际目标/合成Authorization判定，未使用真实key。
- mock-v1/full-request-diff.json：40组逐组结果；仅单列model，未删除prompt字段或参数。
- gate-tests/summary.json：10项只读配置/预检/模型与provider匹配/运行绑定检查通过。
- source-lock.json、input-lock.json：最终代码与287个冻结输入绑定；validator不再要求max_completion_tokens=8192。
- development/tested-before-live-binding：矩阵测试时源码。矩阵后仅增加live run绑定检查和main调用，执行/transport/比较逻辑未改；该新增路径由10项gate检查覆盖，见validation-source-correspondence.json。不把旧测试冒称覆盖新代码。
- SETUP.md、route.example.json、route.openweb.example.json：配置步骤和本地只读预检。用户无需把key贴到聊天。总控安全输入脚本保留在其独立目录，本任务未修改。

旧实验成绩、默认回归负结果和所有CLI失败包保留。开发中一次同路径delete/add patch被工具拒绝，另建dispatcher.py完成，不隐藏该错误。没有模型/EDA功能分数。

正式剩余条件：上游目录审查并固定provider、实际执行进程安全配置凭据与代理、总控审核本包并签入精确源/输入/route的有限技术放行。当前不能因为本地PASS直接上线；待总控独立审核。

官方参考：https://openrouter.ai/docs/guides/routing/provider-selection ，https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties ，https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create 。这些支持API字段说明，不代替账户/内部行为实证。
