# Findings
总控先前三次公开 GET 成功但未保存原 HTTP 响应。read_thread 输出截断，不作为完整目录。现授权保存公开目录，限定每 URL 一次 GET、无密钥、无重试。
官方 https://openrouter.ai/docs/guides/routing/provider-selection 明确 base slug 匹配多变体；精确变体须使用完整 slug。provider_name 不等同 endpoint tag。
完整规则补充：base不自行纳入需显式选择的service tier，三份目录普通OpenAI仅openai，故最终固定openai/OpenAI，未选择最初候选azure/us或高价fast。schema无需修改。
message-transforms文档当前使用context-compression plugin；仅<=8192上下文默认开启，三目标普通端点1050000。最大messages JSON4347bytes，未启用plugins，未测真实token或服务内部转换。
