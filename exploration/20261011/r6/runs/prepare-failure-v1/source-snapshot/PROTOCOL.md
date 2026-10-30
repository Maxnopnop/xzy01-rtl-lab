# R6 冻结准备协议 v1（非执行放行）

研究假设：显式可执行IR可使规格/意图/RTL间的可观察偏差具备阶段关联；是否提高功能准确率或反馈收益由自然模型结果检验，当前不预判。新机制是两票据乱序完成/顺序退休、四拍逐位恢复除法、带独立输入槽与输出背压的标签匹配。不是旧题改位宽/端口/种子；它们增加跨拍旧状态约束和数据/控制耦合，但“更有区分力”只是待检验设计假设。开发前没有模型试题/挑题。

固定原创建模开发集：3机制×2重复；所有设计和校准题明确为development，不是独立最终保留集。候选保留集本轮为空，后续必须另冻结未参与调优的任务。参考同作者，参考路径/总控审核不称外部独立作者。

四臂：S显式JSON IR→首次RTL→F/R；D直接RTL D1→无条件重生成D2→F/R。D2固定父样本，不select-best，即便D1合法通过或非法都使用D2继续。各策略6例主分母、18调用机会，半共享12；共享合计48唯一调用。S/F与D/F最终获得同一公开RTL_spec检查字段（最多8公开差异），IR私有诊断只后评分。S/R与D/R同候选但不给执行结果。前三阶段设计事实/公开例子一致；最终分支S不额外带IR。这是显式IR流程vs两次RTL尝试，不是纯格式因素；无显式IR不等于无内部思考。

IR支持域沿新目录intent.py冻结：单模块端口，最多16个1..8位寄存器，16KiB JSON，唯一键，disjoint/complete rising/falling银行，有限表达式AST且无eval/exec/call/数组。assignment按宽度wrap/并行旧状态；reset可表达async_low/sync_low/none，不支持类型归UNSUPPORTED。实现任务仅rising、async_low。format/IR_INVALID/UNSUPPORTED/INPUT_LIMIT/EXTRACTION_ERROR/编译或功能失败都保留，不剔样；限额导致未模型调用也保留原计划分母。

后评分S三路IR_spec/RTL_spec/RTL_intent：ALL_MATCH；IR_SPEC_DIVERGENCE_RTL_FOLLOWS_IR；RTL_IMPLEMENTATION_DIVERGENCE；RTL_CORRECT_DESPITE_IR_DIVERGENCE；BOTH_DIVERGE_UNATTRIBUTED；REFERENCE_OR_ALIGNMENT_CONFLICT；NOT_ASSESSABLE；其他OBSERVABLE_DIVERGENCE。仅可观察关联，不直接证明模型内部理解因果。D无IR不可定位理解阶段。反馈配对help/harm/no_change仅两臂都有功能可评分状态，否则inconclusive；完整分母/未启动/未知单列。首次及最终、表示对比与stage分析均按固定计划报告，不按成绩选子集。

准备0真实调用。未来仅总控精确plan SHA放行后最多48串行gpt-5.6-sol/low，180秒/次，总派发10800秒，单prompt256KiB、stdout+stderr软上限2MiB、原RTL提取128KiB，磁盘750MiB派发前检查。CLI没有发送temperature/seed/max_output_tokens，不能把记录字节上限称服务token硬上限；CLI自身可能内重连，48是逻辑预约不是底层HTTP请求计数。账户snapshot不是额度保证。前4真实返回仅服务gate，不按功能/格式成绩筛选；服务异常/403/未知立即停止，无定时重试/重发/切模型/补样/扩批/充值。

新stream_process/cli_adapter保存原字节、chunks时间/哈希、请求nonce/SHA/模型/可执行文件及本地PID身份/退出凭据，关键文件atomic+fsync，仍可能丢失宿主被终止瞬间的数据。不保存login auth probe输出/密钥，环境只传既有trusted CLI，不改机器配置。恢复取得批锁和调用writer锁、检查本批PID创建身份后只读检查；活进程拒收尾。只在零退出、闭合流、请求/事件/最终文件一致、一个clean completed且无工具、usage可核对时离线重建，标来源；其余UNKNOWN且usage=null。中断过的批不自动续派；recover脚本向新输出目录写重建材料，不改原证据，不调用模型。仅清理保留句柄的本调用直接子进程，完整后代清理UNVERIFIED，不承诺生产恢复或桌面根因已修。

实际token/cache/reasoning、已知子账与未知费用分开；cached包含在input，reasoning包含在output，不额外相加。不称严格token公平。未提供的provider字段保持null，金额UNKNOWN，不从订阅/零credit推断免费。

覆盖：固定binary/#2采样、小参数、有界短序列及部分定向路径。除法正常无暂停的全部16×16输入对作有限域检查，不等于所有交错暂停/start/reset；队列和join未状态×输入穷尽、未无界证明、无PPA/学校EDA。随机轨迹与手推/定向见证分别说明，向量数量不证明完整。

资源：快照24逻辑CPU/约31.4GiB RAM，离线Icarus串行、独立校准最多2作业并行（写者及其子另计），编译15s/模拟10s/校准子进程最多6s，准备总时限10800s、软内存预算2GiB（无OS硬配额）；本机占用和配置不改变。必要test_lab/test_batch/test_dev/test_fsm仅默认环境一次，失败及skip保留、不隔离重试。准备完成即停供独立总控审核。
