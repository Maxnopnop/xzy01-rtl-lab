# 提示词统一审核入口

本材料沿用同一轮三次离线渲染，无追加渲染。agents.enabled=false 后三准确模型输出列表完全一致（仅删除顶层消息 id），逐角色逐内容 diff 见 per-message-diff.json。未修改导出的原始 JSON；规范化副本单列。

触发定位：历史额外两条 developer 均为多代理角色/模式指令，本轮从实际入口关闭 agents.enabled 后消失。此为配置层证据，未定位安装二进制内部精确源码分支；不把模型能力推断写成已证实的内部机制。

技能说明、环境上下文保持三模型一致而未删除。工具 schema 与最终基础 instructions 封装未出现在 prompt-input 列表，故不宣称全请求已统一或纯 system/user 已实现。短 prompt 的一致性尚不能覆盖全部正式题目/RAG输入，更不能替代真实发送审计。本轮次数已用完，不再渲染新配置。

原 all20 冻结 packet 全部条目只读重算核验，见 frozen-packet-check.json（报告实际数量及 mismatch）。未修改原题、RAG、冻结 system/user 或生产源。

提示词关卡状态：可观测短 prompt 列表一致；完整正式请求一致性 UNVERIFIED。硬8192与零重试保留为后续独立关卡，正式实验 BLOCKED；无 technical-release 或模型请求。

下一步需总控先审核本材料并决定是否授权进一步离线完整请求封装审计，或提供满足完整输入、硬cap与零重试的API接入。本轮不自行追加工作。
