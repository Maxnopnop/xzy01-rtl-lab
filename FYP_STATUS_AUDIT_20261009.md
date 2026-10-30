# XZY01 FYP 总体状态核查

核查日期：2026-10-09（Asia/Shanghai）。项目：Using LLM for Digital Chip Design；导师：Xie Zhiyao。

## 核查范围与结论

现有仓库为 `E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch`，HEAD 为 `aa6ff55`。读取了 AGENTS.md、README.md、ARCHITECTURE.md 和三个根计划文件。`gh repo view` 返回私有仓库 `isPrivate=true`。原有三份计划文件修改及未跟踪 elec_common.py、elec_menu.sh、elec_school.py 均保留。

已完成本机工具链、两模型开发 pilot、FSM 可行性研究、固定错误 IR 的配对修复研究与人工故障校准；同一个历史模型样本已通过 VCS/Xcelium 单例仿真。DC/Genus 已启动验证并准备就绪包，但本机 registry imports 为空，四包 attempts 均为 0，尚无可核验的真实综合回传。正式方法结论、独立最终评估和最终 FYP 交付仍未完成。

本轮重新统计逐项 result.json，执行只读 paired_audit 和 mutation verify；未重新调用模型或重跑学校 EDA。其他历史仿真/综合成绩来自保存证据，不声称本轮全部重新执行。Proposal 对照依据现存提取文本 [proposal.txt](../../work/proposal-review/proposal.txt)，未声称再次核对其原 PDF 版式或最终提交版本。

## 已有成果与证据索引

| 成果 | 核实结果 | 证据 | 范围限制 |
|---|---|---|---|
| 本机工具链/API/原文输入/GUI | 已实现生成、固定测试、Yosys replay、预算与来源绑定、报告和单例运输 | README.md、ARCHITECTURE.md、FYP_ONE_COMMAND.md；evidence/fyp-one-command-20261009；evidence/ece-synthesis-integration-20261009/verification.json | 回归中的模拟 HTTP 不代表所有真实 API 端点已认证；任意提示词生成无固定测试时为未验证 |
| 版本化 Dev10 | VerilogEval 5 + RTLLM 5；来源、许可、划分锁及适配记录存在 | benchmarks/dev10/README.md；evidence/development_audit.json | 开发子集，不能当官方全量 benchmark；参考/人工错误用于工具校准 |
| 两模型 pilot | sol、terra 各 30 份；各 24 功能 PASS、30 Yosys SYNTH_PASS；总计48 PASS/9 COMPILE_FAIL/3 FUNCTION_FAIL | evidence/pilot60/pilot-summary.json；generated/**/*.result.json | 60 次真实生成；编译失败 RTL 可能被综合工具接受，阶段分开报告 |
| FSM 可行性 | 48 模型调用、24 RTL；prose 7/8、table 7/8、checked_table 8/8；综合24/24 | evidence/fsm48/summary.json、synthesis-summary.json；FSM_FINDINGS.md | 仅两个复用开发题；检查组初始 IR 全正确，未触发修复；等调用不等 token |
| 固定错误 IR 配对 | A32+B64槽位；94有效 RTL、2 TIMEOUT；89功能 PASS、94综合 PASS；42双方通过、5仅反馈通过、0仅控制通过、1基础设施不完整对 | evidence/paired-a32、paired-b64；PAIRED_FINDINGS.md；validation/fyp-state-audit-20261009/paired-audit.json | 2获益对重复同一自然错误，另3对为注错延迟应答；条件修复非端到端；2超时不删除、不按零计费 |
| 人工故障/定位校准 | 163单处故障；原公开检查漏30；新增12开发例子后163/163检出；25诊断格通过；0模型调用 | evidence/mutation-v1/summary.json、contracts-v2.json、evidence-lock.json；MUTATION_FINDINGS.md | 本轮 verify PASS：412文件、163变体、25格；人工夹具不算模型效果，增强 profile 已拟合开发集 |
| 历史 RTL 重放 | 178保留 RTL；159 PASS、10 FUNCTION_FAIL、9 COMPILE_FAIL；178/178原标签一致 | evidence/ece-workflow-20261008/replay-summary.json | 60+24+94的重放，不能再次计为178份新增模型数据 |
| 学校商业仿真 | 同源 FSM；VCS X-2025.06-SP1、Xcelium23.03-s004各1840检查、0错误、退出0 | evidence/ece-vcs-smoke-20261008/result.json；evidence/ece-xcelium-smoke-20261008/result.json | 仅一个设计；原始RTL功能测试通过，不证明综合网表等价或时序 |
| DC/Genus 启动 | DC X-2025.06-SP2进入shell；Genus21.14-s082_1取得综合许可并进入shell | ECE_SYNTHESIS_STARTUP.md | 用户学校记录；DC具体综合功能许可和真实库加载仍待实跑 |
| DC/Genus 单例包 | 2旧草稿BLOCKED；2新包READY_FOR_SCHOOL_PREFLIGHT；真实回传0 | workflow/synthesis/registry.json、summary.json；workflow/synthesis/NANGATE_SMOKE_README.md | 已有Nangate typical库路径/元数据与10ns smoke SDC；传输就绪不等于综合完成 |
| 新16调用 replay | 4预留API_ERROR，0有效生成，12 pending | evidence/ece-pilot16-20261008-checkpoint/summary.json | 历史HTTP403阻塞；本轮未探测服务或提交剩余调用，不产生方法成绩 |

当前两个新综合包：`synth-dc-20261009T100543Z-d47c8919`、`synth-genus-20261009T100543Z-07992262`。原始样本 `paired-a32/m01__real_overlap__s001__control`，顶层 `sequence_detector`。本輪重新校验包输入锁、原ZIP哈希和CRC，见 `validation/fyp-state-audit-20261009/synthesis-package-audit.json`。

## Proposal 四目标与缺口

| 目标 | 当前状态 | 待完成与验收证据 |
|---|---|---|
| O1：10月31日前工具链、pilot、方向决定 | 本机流程和两模型pilot已完成；学校仿真已一例验证；商业综合待验证 | DC/Genus真实结果；覆盖组合/计数/FSM的学校验证范围按资源决定；书面方向决定、导师讨论及确认记录 |
| O2：版本化评测、独立开发/最终集、多模型比较 | Dev10与开发基线完成；正式最终集未见完成证据 | 40不同最终题为Proposal规划值，约20+20；需来源/许可、近重复审计、参考验证、独立审核、冻结划分后才实验；若改变规模先记原因 |
| O3：聚焦方法、baseline和消融/等预算控制 | 三组可行性和条件修复配对已完成，收益有限且集中 | 独立题族/自然错误；端到端验证；原/增强公开例子×无/有执行反馈消融；两条件同设计事实；调用上限及token/成本报告；与最近邻差异 |
| O4：原型、独立复现、论文与演示 | 本机GUI/CLI与历史证据报告存在 | 明确接入被评估方法、成功/失败/修复演示轨迹；非主要实现者在干净环境重放并签收；完整论文草稿、海报与答辩材料尚未发现完成证据 |

Proposal 内部冲突：封面、§2.2.1/2.2.2及规划要求至少两模型；§1.2.1要求至少四模型。保留冲突，需按正式提交版本/导师决定澄清，不自动加模型或扩大付费预算。Proposal 并未要求一个正向增益作为完成条件。

依Proposal的计划里程碑（不是本轮重新确认的学校通知）：10月31日方向决定；11月下旬评测manifest和基线协议；2027年1月方法原型/进度报告与最终实验前冻结；3月控制评估、误差分析、复现和完整草稿；4–5月报告、海报和演示。当前10月9日适合收敛方向与补齐工具证据，不应以代码量代替FYP完成率。

## 研究判断

当前问题仍是待检验假设：控制调用预算后，结构化状态表和可执行检查能否减少特定时序语义错误，并定位规格→IR或IR→RTL的可观测偏差。现有结果支持实现可行和部分条件修复收益；不支持普遍优势、独立最终集泛化或自然模型定位准确率。有限图IR等价与固定向量RTL仿真证明强度不同；BOTH_DIVERGE不能唯一解释模型内部原因。

2026-10-09重新读取作者arXiv摘要：[VeriRefine](https://arxiv.org/abs/2607.18519v1)已有显式中间规格、审计及理解/代码错误分阶段修复；[LLM-FSM](https://arxiv.org/abs/2602.07032v1)已有FSM行为理解和RTL翻译评测。因此“表+检查+阶段区分”不足以直接称新颖。可继续核验的增量是：受限预算下按错误类型的因果比较、公开反馈与隐藏评分隔离、定位校准和失败边界。现存FSM_LITERATURE.md是初步对照，作者代码/实际预算及完整最近邻复现仍待核查。

## 按优先级的近期任务

1. **P0 DC 单例实跑与回传审阅，然后同源 Genus 单例。** 复用现包与Git下载备用路线，手动一次一例，不批量。分别记录工具启动、综合完成、综合网表功能验证、时序达标；失败也保留可验收证据。
2. **P1 本月方向决策包。** 解决Proposal模型数冲突；整理已有收益/无收益、最近邻差异、目标错误、baseline/control、预算及职责，供导师讨论；不自动联系导师。
3. **P1 最终集/研究协议设计。** 补独立题族和自然错误来源，先冻结选择规则、重复/污染限制、主指标与统计单位；增强公开例子需等信息控制。候选保留两题不能冒充完成40题最终集。
4. **P2 服务恢复和下一轮调用。** 用已有配置做无调用检查；实测调用前明确模型、最大调用、token/费用约束和停止条件。历史403计划与新实验分开，不盲目补跑。
5. **P2 独立复现与写作。** 已有方法/实验/限制可先写；安排队友独立重放的任务材料，但未经用户要求不建chat或发任务。PPA优化、课程Innovus、广泛商业复验均不抢主线资源。

## 最先完成的一项具体工作：DC 单例证据闭环

学校浏览器从[私有仓库备用ZIP](https://github.com/Maxnopnop/xzy01-rtl-lab/blob/main/ece_git_packages/xzy01-synth-local-20261009.zip)下载到学校本地，按 [ECE_SYNTHESIS_GITHUB.md](ECE_SYNTHESIS_GITHUB.md) 核对SHA256（`13b9b9213082c0e81b0388620fbb92b793a274ceb4319be9f9e84de5113f453a`），解压到新目录，执行 `bash start_local_dc.sh`。随后回传returned/中的ZIP及配套JSON；原始session保留。不要重用已超时共享路径作为唯一传入方式。

验收记录至少包括：源RTL/结果/SDC/包哈希、工具版本和退出码、库指纹与PVT/单位、分析与映射日志、网表、面积/时序/约束报告。审阅未解析引用、锁存器、约束覆盖、违例与复位路径豁免。完整退出与产物仅标COMPLETED_REVIEW_REQUIRED；功能须额外网表仿真或等价证据，时序须按明确约束逐项审阅。

10ns为smoke假设，非正式性能目标；rst_n false path未覆盖recovery/removal和复位释放。即使正slack也不能称芯片时序签核。DC证据闭环后，另一次手动执行 `bash start_local_genus.sh` 并同标准验收。目前真实下一步依赖用户学校Horizon会话执行与结果回传。

## 文档一致性及持续记录

README旧§6仍说商业仿真未在学校运行，VCS旧result限制仍写Xcelium未验证；它们是旧时点记录，应由后来的Xcelium证据和本索引解释，不改历史实验原件。ECE_SYNTHESIS_GUIDE旧开头的缺库状态已被新就绪包更新；FYP_FLOW_SUMMARY旧优先级也早于本轮DC/Genus任务。近期维护应以本索引和当前registry为准。

本轮新增核查文档及validation审计输出，更新三个计划文件；没有提交/推送、更改历史RTL/提示词/实验锁、付费调用、学校执行或关机。历史笔记中的关机与扩展授权不适用于当前总控指令。
