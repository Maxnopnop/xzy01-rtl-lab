# R7 固定方法承继与停止规则

承继R6（method-lock.json）：S真实显式JSON IR→首次RTL→F/R；D直接RTL D1→无条件D2→F/R，D2固定父样本，不按功能select-best。F两表示仅同公开RTL_spec字段，最多8公开差异；私有IR_spec/RTL_intent只生成完成后评分。所有臂相同原设计事实/公开事件/模型与三阶段机会；这是IR流程对两次RTL流程，不是纯格式/无内部思考对照。没有实现R7专属prompt、事实改写或隐藏向量。

IR不变：单clk/rst_n，rising/falling disjoint寄存器库，最多16个1..8bit寄存器，16KiB JSON；async_low/sync_low/none；表达式常量0..65535、加减/位运算/常量0..7移位/单比较/布尔/条件，4096字符/512AST节点；无数组/第二独立时钟。部分同步reset可用none与显式rst_n条件表达，不据局部reset误判unsupported。宽寄存器可拆分是潜在表达方式，不把所有16bit端口一概说不可支持。判题R6原全输出逐事件精确比较不变。

分类承继：ALL_MATCH；IR_SPEC_DIVERGENCE_RTL_FOLLOWS_IR；RTL_IMPLEMENTATION_DIVERGENCE；RTL_CORRECT_DESPITE_IR_DIVERGENCE；BOTH_DIVERGE_UNATTRIBUTED；REFERENCE_OR_ALIGNMENT_CONFLICT；NOT_ASSESSABLE；其他OBSERVABLE_DIVERGENCE。观察关联不证明内部理解因果，D无IR不归因理解。收益需自然失败见证与参考复核；没有自然错误则定位收益不可估。paired help/harm/no_change只在两臂功能可判时计算，其余inconclusive。格式、unsupported、INPUT_LIMIT、EXTRACTION_ERROR、IR_INVALID、compile/infra、UNKNOWN、PENDING全部保留原计划分母。

若未来另有合格来源及新审核：最多3机制×2重复/6case/48唯一串行逻辑预约，gpt-5.6-sol/low，每策略6结果/18机会、半共享12（具体更小计划必须重新冻结分母，不能硬保6）。180s/次、10800s派发、750MiB派发前阈值、256KiB输入、2MiB软日志、128KiB提取。前4服务gate只查服务，不用成绩挑样。逻辑预约不是底层HTTP数/token硬配额；实际token/cache/reasoning不同、费用无账单UNKNOWN，cache属input/reasoning属output不得重加。服务403/未知停止，无重发/补样/切模型/自动扩批。

本包实际执行case0、预约0、模型0，不存在可放行execution SHA。48仅准备界。保留R6 stream/engineering-v2与只读保守恢复，不改冻结源或据新候选调方法。若将来改握手判据/IR/提示必须在新development工程验证，接触并影响修改的当前候选不得再称未调优heldout。
