# R3完成：首次候选全通过，两臂无差异

唯一冻结计划24槽全部启动、生成、评分：8个共享首次RTL、8个重新生成、8个公开执行反馈输出。全部在固定隐藏事件测试上PASS。首次候选分类为有界测试正确8、自然功能错误0、非法RTL/编译失败0、基础设施/未知失败0、未启动0；不能把“有界测试正确”写成无界证明。两臂各8/8 PASS；全8对help=0、harm=0、no_change=8、inconclusive=0。没有自然错误修复样本，不从这个全正确批次估计修复能力或宣称反馈收益。

| 家族 | 两次首次候选 | 重复1：重新生成 / 反馈 | 重复2：重新生成 / 反馈 | 家族内配对 |
|---|---|---|---|---|
| cancel_deadline | PASS / PASS | PASS / PASS | PASS / PASS | 无变化2 |
| retrigger_window | PASS / PASS | PASS / PASS | PASS / PASS | 无变化2 |
| elastic_slot | PASS / PASS | PASS / PASS | PASS / PASS | 无变化2 |
| rotating_owner | PASS / PASS | PASS / PASS | PASS / PASS | 无变化2 |

四个开发家族每家族仅两个重复，共享文字规格、作者及有限判据。首次和两个分支也共享候选，不是24个独立任务。机制支持域确有增加，但本轮没有证明新题更难；仍有天花板。两臂共享事实、公开例子及期望、完整首次响应和实现指令，额外公开执行结果是唯一处理差异；不称同文本。全部候选未按对错筛选，全部生成结束后才统一隐藏评分，未给模型隐藏反例，也无输出长度筛样。

实际唯一调用账（24次）：input=272882，output=8245，cached input=155904，cache-write input=0，reasoning output=194。shared首次8次：input=88892、output=2977、cached=44544、reasoning=194。字段按CLI原样报告，cache/reasoning不再次与所属input/output相加。实际费用UNKNOWN，无账单；请求模型gpt-5.6-sol/low，CLI未暴露后端snapshot，无硬token cap。

| 成本/机会 | 重新生成 | 反馈 |
|---|---:|---:|
| 本臂实际分支调用 | 8 | 8 |
| 每策略首次+分支机会账 | 16 | 16 |
| 分支 input / output | 91839 / 2682 | 92151 / 2586 |
| 分支 cached / reasoning | 51968 / 0 | 59392 / 0 |
| 完整共享首次+分支 input / output | 180731 / 5659 | 181043 / 5563 |
| 完整共享首次+分支 cached / reasoning | 96512 / 194 | 103936 / 194 |
| 半共享分摊 input / output | 136285 / 4170.5 | 136597 / 4074.5 |
| 半共享分摊 cached / reasoning | 74240 / 97 | 81664 / 97 |
| 分支adapter耗时（秒） | 91.904 | 93.186 |
| 完整共享首次+分支adapter耗时（秒） | 178.026 | 179.308 |
| PASS / 1000半共享分摊output tokens | 1.918 | 1.963 |
| 费用 | UNKNOWN | UNKNOWN |

两个16机会账相加32不能当作实际调用数；共享首次实际只运行8次。半共享分摊是账本约定，不是一次可部署策略的完整支出。output成本效率的小差异来自实际输出长度，不是功能收益或费用优势。缓存与输入不等，不能宣称严格等token、算力或费用。实际adapter总耗时271.212秒，generation总253.439秒；campaign启动至原始隐藏结果落盘297.661秒（主机文件时间），run约3.34MB，在预声明24调用/90分钟派发/500MiB预算内。

本次真实工具评估32次（8公开首次检查+24隐藏评分），32次编译及32次仿真均正常退出、nonce/count/errors收据一致。准备校准另有28编译评估/26仿真；控制54mock仍不计真实模型或仿真。Yosys NOT_RUN，不推断综合性/PPA。

原runner在24项结果落盘后汇总exit1：judge.stage=simulate覆盖生成角色stage，配对筛选失败。原源码、协议、响应、judge与results.json均冻结保留；仅以plan逐id恢复角色，在run外另存汇总并封存证据，无模型/仿真重跑。[收尾记录](FINALIZATION_AMENDMENT.md)明确原mock测试未覆盖此元数据冲突，不能把其PASS当作全面工程验收。恢复出的全部功能状态与原judge完全相同。

独立审计通过975份本次证据、24个prompt/request/原响应/usage绑定、8对提示词反馈增量、32份compile/sim收据、全部公开/隐藏向量逐字段绑定；旧R1/R1b/R1c/R2共4953份文件及源码锁保持一致。旧403记录、R1c的64份无新增错误、失败校准v1及R2唯一harm均未改。

范围修正：[SCOPE_ERRATA.md](SCOPE_ERRATA.md)。仲裁器两参考的可达编码相同，只支持等价实现写法校准，不是不同状态编码。公开检查对人工cancel/finish优先级突变的漏检保留（7/8），没有据隐藏成绩补公开例子；本次公开8/8 PASS不消除这个已知盲点。首次RTL支持多端口/组合ready，但不直接测状态表收益、IR/RTL阶段定位；与R2同时改变了候选来源、支持域与反馈载体，不能作复杂度的单因素因果推断。

最近邻差异见[原始文献核查](LITERATURE_CHECK.md)：[VeriRefine](https://arxiv.org/html/2607.18519v1)审计逐信号ASTF并按错误阶段反馈，[AutoFSM](https://arxiv.org/abs/2512.11398)使用IR翻译及SystemC测试，[LLM-FSM](https://arxiv.org/abs/2602.07032)由结构化YAML构造大规模FSM规格/参考。本轮没有复现其框架、任务或预算，也不声称性能可比或方法新颖。可支持的结论仅是这个有限、全首次正确集合上未观察到公开执行反馈收益。

后续研究方向（建议，不执行）：

1. 优先研究公开检查的覆盖与独立参考可信度：事件竞争盲点已有人工见证，适合预声明机制覆盖审计；与LLM收益分开，不用本批隐藏结果反向补公开例子。
2. 若继续研究结构化时序意图，另设计信号时序契约/结构IR与RTL执行反馈的正交对照，保留同起点重新生成；ASTF和阶段反馈已有近邻，需明确新的可验证差异。当前R3不能支持该方向的收益主张。
3. 将预算机会、候选完整分母和运行器证据链作为评价要求；先修复新版本的角色/判题字段隔离与异常格式分类测试，再考虑新的事前固定机制集。不能为制造自然失败择题或按功能结果无限扩样。

本批结束，不自动扩大或复跑旧题。

原始索引：[冻结计划](runs/prepared-v1/plan.json)、[原始24项结果](runs/prepared-v1/results.json)、[全部job目录索引](../r3-corrected-results.json)、[角色修正与预声明汇总](../r3-summary.json)、[独立审计](../r3-analysis.json)、[收尾证据绑定](../r3-finalization.json)、[证据锁](runs/prepared-v1/evidence-lock.json)。每job的response.txt、generation.json、call日志、hidden-judge.json及收据保留；首次另有public反馈及检查产物。
