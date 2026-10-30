# 阶段A：生产登录与本地捕获对应审计

**结论：BLOCKED_AT_PRODUCTION_CORRESPONDENCE。按授权的阶段A停止条件结束；没有启动新CLI、mock、失败槽或真实模型。缓存及240预算修订沿用总控已验收结果，没有重复运行或覆盖。**

## 为什么不能进入B/C

correspondence-matrix.json逐项对照基础instructions、角色正文、技能权限环境、嵌入工具、reasoning/其他生成字段、provider/auth、传输及重试。

历史成功接入仅说明内置openai登录通道可返回OK，未提供完整发送body。旧失败日志则直接证明该登录通道有WebSocket连接错误、Reconnecting及HTTP回退。自定义mock显式禁WebSocket、无需认证、使用/v1/responses，并允许自定义provider重试字段；这些条件没有与内置登录通道一一对应。旧内置provider覆写错误也是实证，不能把自定义retry0套用到生产。

本机codex_network_adapter.py只读源码仍通过builtin openai和forced_login_method=chatgpt；外层一次run_process不能保证CLI内部只发一次。generate()还会拼额外指令、配置reasoning，不能直接当新冻结协议适配器。该源仅作为关联代码，未执行、未修改，也不是已经批准的240槽执行源。

在现有官方配置/认证说明与本机证据中，没有找到可证明固定内置登录分支完整请求构造及禁重连的离线接口。官方支持custom provider使用OpenAI认证，但“支持这种认证”不证明两条发送/重试实现相同；不得为了捕获读取复制auth或把真实凭据发送给本地mock。因此本轮没有满足进入B/C的前置条件。

## 精确未完成项

1. 三准确模型同题同条件的生产完整body（包括嵌入input的tools）及影响生成的公共字段可比证据；目前只有Luna历史mock，不能生成真实三模型diff。
2. 内置生产provider关闭HTTP/stream重试、WebSocket重连、fallback补发及自动续写的支持证据；历史明确存在重连，当前没有经过验证的修复。18个custom HTTP失败槽即使通过也不证明这一点。
3. CLI将system正文放developer及公共附加内容/默认参数的协议偏差处理；不得仅跨模型一样就追认旧协议。

最小所需接口是同一生产分支的受支持离线完整请求构造导出，加上可验证的内层零重试控制。另一条可审路线是明确换为能暴露完整原始请求且控制重试的API适配器，但账户/API权限与路线切换仍须总控审查；本轮不替换登录方式、模型或原题RAG，也不作新的接入调用。没有可证生产对应关系时继续堆mock不构成进展，因此按阶段A明确停止。

## 保留的后续边界

B上限1候选×3，条件满足才40×3；C上限3模型×6失败类型=18槽，观察完整窗口；本轮均0，标NOT_STARTED，不能标PASS。D技术放行不存在；“通过后执行”的人类授权保留，未要求重复确认意图。原次序前三槽只能在总控签入本次适配技术放行后启用，计入240，不额外探针。

预算已采用240机会/实际usage，8192不是阻塞；不重建240payload、不改旧锁或新预算。来源清单source-lock.json绑定本轮实际阅读的回执/配置/日志/源码；historical-retry-evidence.json仅提取历史日志事件，不把重连日志数当付费模型调用数。没有重跑原280/752等全量hash审计，沿用总控独立验收并绑定其回执。

官方已读取：https://learn.chatgpt.com/docs/auth （认证模式有别）；https://learn.chatgpt.com/docs/config-file/config-advanced （provider定义决定wire/auth/endpoint；内置ID不能覆盖）；https://learn.chatgpt.com/docs/developer-commands （prompt-input只列消息输入，send-message-v2会发turn，不适合无推理约束）。本结论限定当前证据，不声称所有CLI版本永远无法做到。
