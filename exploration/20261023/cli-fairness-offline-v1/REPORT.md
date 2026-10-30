# CLI 公平性有界离线审计（2026-10-23）

结论：BLOCKED。一次配置方案、三个准确模型各一次 debug prompt-input；全部 exit0，没有模型生成、探针、校准或正式 dispatcher。只写本独立目录。

历史 UTF-8 JSON 去掉每条消息顶层 id 后：Luna 3 条，Terra/Sol 5 条；Terra/Sol 内容相同，移除额外两条 developer 多代理指令后与 Luna 一致。详细原文差异保留 historical-comparison.json。旧目录 7 个直接文件逐个前后 SHA 相同；未进行所有历史包全量复审，不将只读操作夸大为全部证据重新验证。

## 本次验证的配置

在独立 CODEX_HOME（仅复制既有模型目录缓存，没有复制认证）与独立工作目录，使用同一 instructions 文件、相同显式短 prompt、同一 low reasoning 设置。准确命令见三个 *-command.json。

- agents.enabled=false
- features.shell_tool=false
- web_search="disabled"
- model_reasoning_effort="low"
- model_instructions_file 指向本审计 work/instructions.txt

三次渲染均为 developer/user/user 三条，去掉顶层消息 id 后完全相同。agents.enabled=false 在本机渲染上消除了所见两条多代理指令。其他工具配置被本命令接受，但 prompt-input 不展示完整工具定义，不能据此宣称已证明所有工具关闭。技能目录和环境上下文仍存在；未进行第二种配置或反复试错。本次短 prompt 仅用于离线渲染，未替换正式题目、RAG、system/user 资产。

## 未解决项

1. 离线 prompt-input 是输入列表渲染，不是实际发送请求抓取，也不展示全部请求参数、服务端输入或基础 instructions 的最终封装。相同渲染不能直接证明生产发送严格两角色且完整一致。
2. 本次核查的官方配置参考未给出 max_output_tokens 字段。features.rollout_budget 是预算跟踪及提醒设置，不足以证明单请求 visible+reasoning 8192 服务端硬截断。旧 cli-cap-v1 的 schema 搜索结论仍作为历史证据，不重新生成 schema。未知不等于断言所有版本永远不支持。
3. 历史 model_providers.openai.request_max_retries/stream_max_retries=0 被本机拒绝，因为内置 provider ID 禁止覆盖。失败原文与 hash 见 prior-retry-config-failure.json；不重复失败启动。官方自定义 provider 的重试字段存在，不能转而推定当前已登录 ChatGPT 内置通道零重试，也不能证明一 CLI turn 只有一次推理。没有创建自定义认证通道、读取凭据或再次调用模型。

## 需要总控决定的路径

保持原协议：提供三准确模型有权限的 API 接入，使用可审计的完整固定请求、受支持的 8192 completion（含推理）服务端硬上限及客户端零重试；先审计实际适配协议和权限依据，再由总控放行原预算内请求。此前 API 401 仍是独立认证失败，不能用 CLI OK 替代 API 权限证明。

若坚持当前 CLI：需要另行明确批准修改完整消息定义、token 上限性质及自动重连/调用计数规则；这会改变原协议，不能由本审计擅自实施。把 prompt 写“最多8192”、超时杀进程或事后检查 usage，都不能代替硬输出上限。当前不创建 technical-release、不预约正式槽位、不启动模型请求、不增加候选。

官方来源（本次已读取）：
- https://learn.chatgpt.com/docs/config-file/config-reference — agents.enabled、shell_tool、rollout budget、provider 重试配置；只支持相应配置说明，不构成本地实际发送证据。
- https://learn.chatgpt.com/docs/developer-commands — debug prompt-input 的离线输入列表渲染用途。

入口 audit.json、render-receipts.json、render-normalized.json。默认回归失败、旧403及重连记录均未改写。待总控审核；本报告不构成实验放行。
