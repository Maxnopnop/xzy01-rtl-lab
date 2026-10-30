# 路由依据（待总控独立审核）
官方 https://openrouter.ai/docs/guides/routing/provider-selection 的 Base Slug Matching：根 slug 匹配普通变体，但不自行选择需显式加入的服务层端点。完整 region slug 可以限定区域。
三份本次公开目录均仅有一个普通 OpenAI tag=openai，其余 OpenAI 项为 openai/flex 和 openai/fast，service_tier分别flex/priority。故选择 provider.only=[openai]，无service_tier字段；expected_provider=OpenAI 来源于三份目录 provider_name，尚无真实响应核验。不选较贵fast，不更改模型、messages或schema。
早期曾考虑精确azure/us；在完整核对服务层例外规则后未采用。该候选未提交生成或写入生产配置。
https://openrouter.ai/docs/guides/features/message-transforms 当前说明：context-compression按请求启用；上下文不大于8192的端点默认启用。当前三项普通OpenAI上下文1050000，无plugins/transforms/service_tier参数。离线统计提示长度另记。按公开文档无默认压缩触发条件；非服务端内部提示完整性的可观察证明，账户设置、网关内部重试及上游权重身份仍不可由客户端证明。
allow_fallbacks=false 和 require_parameters=true 由原dispatcher添加。实际返回provider必须精确OpenAI，否则停；这个返回名本身不能证明具体底层机器或无内部重试。不得另加生成探针。
