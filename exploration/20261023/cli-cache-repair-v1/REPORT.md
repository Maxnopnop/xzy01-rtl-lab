# 缓存修复与有限离线审计（2026-10-23）

**结论：缓存兼容已修复；完整生产提示词与生产零自动重试仍 BLOCKED。没有真实模型调用、正式预约、technical-release 或生产执行。取消8192硬cap已纳入独立预算修订，不再作为本轮阻塞。**

## 缓存来源与修复

原cli-request-capture-v1使用的缓存来自0.163.0，npm实际二进制是0.147.0。三个准确模型的旧目录均没有supports_parallel_tool_calls。固定原npm二进制hash，按本机help和官方文档运行一次debug models --bundled，直接保存原始stdout为bundled-catalog.json，再用受支持model_catalog_json指定它。三个模型原生字段均true；未人工补值、改模型或升级。catalog-provenance.json逐字段记录来源/有无/一致性，catalog-receipt.json绑定命令和二进制SHA。目录能力不等于账户模型权限。

两候选实际stderr都不再出现cache parse error。缓存问题已经与后续阻塞分离。

## 有限捕获与停止

固定同一npm0.147二进制，两候选各只启动Luna一次、捕获一个本地/v1/responses请求。请求使用冻结Prob023/no_rag真实system和user，system复制到独立临时instructions文件，不修改冻结源；reasoning参数省略。每个候选内部计划固定同cwd、环境与配置供三模型，因停止未实际启动Terra/Sol。

候选1：原生catalog，更新检查关闭、remote_plugin关闭、apps关闭；本地代理仍拒绝chatgpt.com和github.com CONNECT，立即停止。

候选2：在新证据路径中以--ignore-user-config和显式-c传入公共配置，另把受支持chatgpt_base_url指向loopback。发现请求路径是/blocked-chatgpt/plugins/featured?platform=codex（本地GET拒绝），另有github.com CONNECT拒绝。仍停止，不作第三候选。

所有provider模型地址都为本地接收器，接收器不转发，400仅为预声明fixture；无模型答案。全新HOME/CODEX_HOME与系统环境白名单，不读取/复制认证，cli_auth_credentials_store=file只允许该新home文件。代理拒绝连接并保存目标，未建立外网隧道。此为应用配置及本地代理隔离，非OS防火墙审计；不把“观察到的外联均被拒绝”夸大成全系统无任何网络活动。

源码offline_audit.py与offline_audit_candidate2.py、预声明计划、完整request-N.bin、headers、命令、stderr/stdout、退出状态均保存。临时HOME helper alias警告保留。候选1停止后只读分析漏UTF8发生GBK错误，未重跑捕获；根cwd git status不是仓库的错误也保留在progress。正确lab Git状态另查，已有改动未动。

## 哪些关卡没有通过

- 仅Luna两份不同候选请求，不存在三模型实际完整请求对比；跨模型diff为NOT_EVALUABLE，未删除实质字段来构造一致。40组×3最终离线验证未开始。
- 工具定义嵌在input.additional_tools，冻结system在CLI里变成developer；技能/权限/环境附加内容仍存在。mock可见结构不能追认旧system/user协议，也不能证明已登录ChatGPT生产分支同构。
- 原生目录显示Luna/Terra默认reasoning medium、Sol low。这是目录证据；未实际捕获Terra/Sol，不冒称三实际请求已有这些差异。实际Luna带medium/context all_turns，即统一省略配置也可能被CLI插入默认，须另审。
- retry-matrix.json明确列出400只观察到每候选1个POST但提早触发停止，不能证明完成观察窗口内无重试。401/403/429/连接中断/SSE断流均NOT_STARTED；代理CONNECT拒绝不是模型失败矩阵。自定义provider的request_max_retries=0与stream_max_retries=0不能证明内置登录provider同分支，旧内置provider覆写失败保留。

## 新预算修订及离线适配

budget-revision.json保留旧policy路径/hash，只取消8192每次硬cap及其总token上限，改原20×3准确模型×2条件×2样本最多240调用机会。固定原slot/task顺序、并发1、不补样、不自动重试、预约消耗机会、未知停止。保持180秒请求超时、模型阶段/总墙时、响应字节/磁盘等保护；无充值或账户保护变更。

revised-requests/保存240份新版本payload，revised-request-manifest.json逐项绑定原/新SHA。每份仅删除max_completion_tokens，messages和其他字段不变，temperature/seed/reasoning继续省略。这些是离线待审payload，未写原冻结目录，也没有生产transport或dispatcher接入。

budget_adapter.py只进行payload与usage数据适配：保留raw usage，input/output/reasoning/cache/total缺失=null与unknown_fields；0是已观测0；reasoning不重复加到output；价格/费用未知保持null。test_budget_adapter.py五项离线测试通过，覆盖未知、0、嵌套reasoning、坏类型、哈希拒绝与消息不变。它们不是重试测试，也不是模型/EDA测试。

## 保全及总控待审项

preservation.json：旧capture12项、full-prompt19项、addendum8项、all20冻结752项、旧executor1928项全部hash匹配。没有改变历史成绩或失败。

总控可审核缓存修复与预算修订，但不能据此放行正式调用。最小未解决接口是：在固定版本、生产登录通道下取得可比的完整请求构造，并在不依靠通用mock推断的条件下证明禁自动重试/续写/传输补发；此外需要解决或接受并另行冻结CLI角色、公共附加内容和默认参数偏差。不能只修模型目录就越过这些关卡。当前有限修复已停止，不新增探针或申请重复测试意图授权。

官方已读依据：https://learn.chatgpt.com/docs/developer-commands （--bundled跳过远端刷新），https://learn.chatgpt.com/docs/config-file/config-reference （model_catalog_json、check_for_update_on_startup、remote_plugin、chatgpt_base_url），https://learn.chatgpt.com/docs/config-file/config-advanced （custom providers）。本机失败优先作为实际行为证据保留，文档不代替发送链证明。
