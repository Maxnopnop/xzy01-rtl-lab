# 核查

旧 v2 固定三模型及 OpenAI provider；直接共享目录运行。不得修改旧已锁源码。
学校四工具真实记录已确认 HOME 单 ZIP → 手动单工具 → 平铺 return ZIP/sidecar；VCS212/Xcelium211 对预期213仍 CHECK_COUNT_DIFFERENT。
官方端点文档 https://openrouter.ai/docs/api/api-reference/endpoints/list-all-endpoints-for-a-model 和 https://openrouter.ai/docs/guides/routing/provider-selection：作者 namespace 与 provider tag 分离，端点 supported_parameters 必须独立核验。

公开GET实际结果：DeepSeek v3.1有deepinfra/fp4等upstream，不能把deepseek当provider。Claude sonnet4返回空endpoints，拒绝导入；4.5另有可用目录项用于离线示例，非自动替换实验。实际账户访问未探测。全部原始metadata+source时间SHA已保存。
