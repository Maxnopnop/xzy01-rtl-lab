# 完整提示词适配：负结果（2026-10-23）

状态 BLOCKED_PROMPT_PROTOCOL_NOT_SATISFIED。预声明最多2候选/6探查，实际1候选/3次离线 debug prompt-input，均exit0。没有进入40组×3模型阶段，没有模型/HTTP生成/app-server turn，没有预算或重试实现。旧封存文件不变，752条 SHA 全部匹配。

## 具体结果

采用项目外同一 cwd 与独立 CODEX_HOME、同一缓存/配置，准确 Luna/Terra/Sol；实际 npm CLI --version 是0.147.0，不能把旧桌面0.163 schema当这个入口的能力证明。版本、启动器hash、命令、配置、原始stdout/stderr均保留。

以冻结 Prob023_vector100r/no_rag 的真实 system 写入外部临时 instructions 文件，user 原文直接作为参数，无OK替代、无原文修改。最终user逐字一致；三列表仅去顶层id后完全一致。外部 instructions 的UTF8 hash与冻结system内容对应，但最终请求instructions字段和角色封装未观察到，不能宣称system已按冻结协议发送。

候选含 agents.enabled=false、project_doc_max_bytes=0、skills.config按官方文档指定技能目录enabled=false，以及shell/web/image关闭。项目外cwd消除了上一轮继承的仓库AGENTS内容（无单独消融，不能将效果全部归给单一开关）。技能目录仍然存在；该配置在所测入口没有达到禁技能目标，未证明普遍不支持。developer还包含权限说明；user环境上下文仍存在。三个角色developer/user/user不等于冻结system/user。

stderr保留临时CODEX_HOME不允许创建PATH helper aliases警告。没有为消除警告重试。未删除或改写原始导出JSON；规范化副本、逐字段diff另存。

## 静态能力与停止依据

已读官方配置参考：project_doc_max_bytes限制项目指令读取，skills.config是逐技能开关，model_instructions_file可指定基础指令。配置参考搜索environment_context无匹配，不能据此断言所有版本永远不能关闭；但本轮没有找到经文档支持的关闭环境注入/导出完整请求开关，故不猜参数。第二候选未提出，也未消耗剩余探查次数。

prompt-input实际只返回消息列表，不含最终request.instructions或tools schema。关闭若干工具不能证明完整tools=[]。旧ThreadStartParams含baseInstructions/developerInstructions/dynamicTools等仅为另一个二进制历史接口线索，未运行app-server，不构成当前CLI全请求证据。

因此未达到进入120渲染的前置条件，提前停止。完整模型服务内部行为亦不可观察，不作已证声明。

## 总控审核所需决定

若冻结system/user和无附加消息保持不变，需要能提供原始messages输入及完整请求instructions/tools可审计证据的接入适配器；当前所测CLI入口未证明具备这些能力。可另审API适配路线，不能把ChatGPT登录成功当API已可用。若改为容许CLI技能/权限/环境附加消息或不同角色封装，属于协议调整，应另审新版本而非追认冻结包合规。本轮没有实施任何调整。预算/零重试关卡保留，尚未进入实现。

官方来源：https://learn.chatgpt.com/docs/config-file/config-reference 与 https://learn.chatgpt.com/docs/developer-commands 。文档与本机行为有差异时保留观测，不以文档覆盖失败。

核验入口：audit.json、field-diff.json、receipts.json、candidate-1.toml、environment-binding.json。等待总控独立审核，不放行正式实验。
