# R6 单次有限批结果（完成后停止）

本批状态 **COMPLETE**：48固定槽中 **48 次clean完整返回、0 个异常/未知预约、0 个未启动、0 个输入限制未调用**。原driver dispatch为 `GENERATION_COMPLETE`。仅运行总控放行的engineering-v2/runner.py → runs/prepared-v2，精确SHA `f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4`；未运行v1/R5、不重发/补样/改题/切模型/扩批。

## 服务与保全

首4production服务gate：PASS。各clean返回均单CLI thread/单clean completed，原chunk/nonce/exit/final/prompt/父样本/模板/model核对通过；不是功能择样。实际CLI版本：{"codex-cli 0.162.0-alpha.17.2": 48}；exe SHA：{"d13914ced6c7af174d8d638db938284231227312104b06a25e9608c632a7daec": 48}。requested model=gpt-5.6-sol/low，后端snapshot未暴露。

只读审计PASS：41冻结源、1491准备绑定、16445历史绑定未变，当前运行2024文件精确集合封存。实际本批compile 72 / simulate 72，326368原事件检查；nonce/退出/DUT/TB/vector和固定公开/隐藏期望、真实IR期望绑定。审计0模型/0模拟/0judge重跑。

## 四臂与各阶段

| 策略 | PASS / 主分母 | 全状态 | 计划机会 | 实际预约半共享 | 已知完成半共享 |
|---|---:|---|---:|---:|---:|
| S-R | 6 / 6 | {"PASS": 6} | 18 | 12.0 | 12.0 |
| S-F | 6 / 6 | {"PASS": 6} | 18 | 12.0 | 12.0 |
| D-R | 6 / 6 | {"PASS": 6} | 18 | 12.0 | 12.0 |
| D-F | 6 / 6 | {"PASS": 6} | 18 | 12.0 | 12.0 |

S=真实模型IR→首次RTL→最终；D=D1→无条件D2→最终。D2固定父，不select-best；F两表示仅同公开RTL_spec信息，R无执行结果，IR专属私有诊断仅后评分。每策略18机会/半共享计划12，不是严格token公平或纯格式单因素。

| 阶段 | 原状态计数 |
|---|---|
| intent | {"PASS": 6} |
| first_rtl | {"PASS": 6} |
| direct_first | {"PASS": 6} |
| direct_second | {"PASS": 6} |
| branch | {"PASS": 24} |

| 任务族 | 全流水线槽状态（不是最终策略通过率） |
|---|---|
| ordered_retire | {"PASS": 16} |
| restoring_divide | {"PASS": 16} |
| tagged_join | {"PASS": 16} |

F/R配对：help **0**、harm **0**、no_change **12**、inconclusive **0**。no_change仅表示两者功能PASS/非PASS分类无改善，不等于RTL相同或所有行为等价。

同case/同最终arm的S/D配对：{"same_pass_class": 12}。这是工作流程对照；无显式IR不表示无内部思考，D不可归因理解阶段。

## 自然三路偏差与研究结论

S原三路观察18项（复用6份真实IR，并非18个独立意图样本）：{"ALL_MATCH": 18}。IR_spec/RTL_spec/RTL_intent都是原固定判据；分类仅可观察阶段关联，不能唯一证明内部理解错误因果。IR format/unsupported/INPUT_LIMIT均在主分母，不因不可定位删除。

本批没有观察到公开执行反馈的准确率改善；保留harm及无变化/不可判定配对，不能推断反馈普遍无用。

最终配对没有观察到显式IR流程优于两次直接RTL流程的功能通过分类；同PASS/非PASS分类不证明一般等效。

没有自然可评分三路偏差样本；人工负例校准不能替代自然阶段定位收益。

## 已知/未知费用账

已知clean返回usage：{"input_tokens": 546955, "output_tokens": 44818, "cached_input_tokens": 299904, "cache_write_input_tokens": 0, "reasoning_output_tokens": 9716}；clean返回缺失字段计数：{"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "reasoning_output_tokens": 0}。整批已预约provider usage：{"input_tokens": 546955, "output_tokens": 44818, "cached_input_tokens": 299904, "cache_write_input_tokens": 0, "reasoning_output_tokens": 9716}；金额 **UNKNOWN**。未知预约usage保持null，不填0、不由标价/订阅/信用余额估算费用。cached input在input内，reasoning在output内，不重加。

| 策略 | 已知半共享 input | output | cached input | reasoning output（output内） |
|---|---:|---:|---:|---:|
| S-R | 136438.5 | 11537.0 | 77952.0 | 3201.5 |
| S-F | 136690.5 | 11489.0 | 70528.0 | 3118.5 |
| D-R | 136787.0 | 11039.5 | 68288.0 | 1837.0 |
| D-F | 137039.0 | 10752.5 | 83136.0 | 1559.0 |

上述子账按shared/2+branch分摊并与实际唯一clean usage守恒；计划机会不冒充已预约数。已知CLI进程时间合计981.317s、adapter合计1010.906s；不是服务端账单耗时。实际prompt字节范围[3478, 7384]，不证明256KiB服务上下文边界。

## 限制与停止

全部是参与本轮设计/校准的原创development，候选保留集为空；同作者三路径参考存在共误读，非外部独立作者/独立最终集。binary/#2/固定参数/有界短轨迹，除法正常16×16有限域不覆盖全部暂停/复位交错；覆盖矩阵已记不可观察规则和缺口，无无界证明/PPA。工程人工验收不是自然模型收益或生产恢复/后代树清理/桌面停止根因修复。默认回归34测试3failure/1error/2skip仍保留；此次未隔离重试或重复回归。

本批执行及报告完成即停，交总控独立核验原stream/CLI/评分/预算/研究价值；不追加新轮、扩批、补样或重判旧模型RTL。原始结果在 `../runs/prepared-v2/results.json`、`summary.json`、`evidence-lock.json`；本报告只在execution-v2新目录写入。

只读审计首版audit-invocation-v1因job根目录exact-prompt路径假设失败；原脚本/完整stdout/stderr/receipt封存，新analyze_v2只修正审计路径，不改原批结果或重跑判题。审计入口：[actual-analysis.json](actual-analysis.json)、[service-gate-audit.json](service-gate-audit.json)、[release.json](release.json)、[analyze_v2.py](analyze_v2.py)。用analyze_v2.py --verify复算只读核验，不覆盖既有审计。
