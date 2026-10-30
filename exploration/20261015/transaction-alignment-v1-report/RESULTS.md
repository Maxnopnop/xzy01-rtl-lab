# transaction-alignment-v1 阶段B单次执行报告（2026-10-15，待总控独立审核）

## 运行与完整分母

阶段A已由总控 ACCEPTED_FINITE_DEVELOPMENT_EXECUTION_PLAN 放行，精确plan SHA c2aeef0482f72c1deded6bf45d6aae6012a889dc4f71801a633e4aa04e942c10。只调用冻结execute.py一次，独占transaction-alignment-v1/run-v1；外层退出0，summary状态COMPLETED_EXPECTATIONS_MATCHED，实际11 IR流式执行、11 Icarus编译、11仿真，33个子进程均退出0、stderr空，0重试/0模型/0新来源候选/0生产修改/default调用。dispatch计时16.766s（不含启动前旧绑定校验），不是外层完整墙钟测量。

完整12描述：11个实际执行且预期匹配，1个case10在运行前已声明规格含糊而不执行。原summary把case10预声明标签放在observed字段，但executed=false明确；**这不是工具观察到SPEC_AMBIGUOUS或自动检测规格歧义的能力**。本报告将它单列，不能宣称“12个校准全部通过”。

| 轴 | 11个已执行观测 | 1个未执行描述 |
|---|---|---|
| IR_spec | 10PASS、1INPUT_PROTOCOL_FAIL | 预声明SPEC_AMBIGUOUS |
| RTL_spec | 7PASS、2FUNCTION_FAIL、1INPUT_PROTOCOL_FAIL、1TRACE_INVALID | 预声明SPEC_AMBIGUOUS |
| IR/RTL事务意图 | 6PASS、2FUNCTION_FAIL、3NOT_EVALUABLE | 预声明NOT_EVALUABLE |

含未执行描述的12分母中NOT_EVALUABLE共4，但真实执行不可评估只有3。FUNCTION_FAIL是预声明人工负例，不是丢弃失败；不可评估和环境失败不能合并成DUT正确率。IR11次指插桩run_stream，原未插桩run没有另行执行。

## 原轨迹支持的结论

case01同构映射与case07部分交付后reset，共320个PRE/POST事件逐字段身份比较无差异。11配对各有80PRE+80POST，native原raw共1760事件，IR输入/打包输出共1760事件，两个域的PRE共各880行；全部原stdout/stderr/argv/started/完成receipt、IR低/高事件、native raw与normalized保留。source driver只用本实现PRE握手推进，不把posedge后输出作当前握手。

- 合法差异：case02 RTL延迟两拍、case03独立双槽队列与IR共享槽不同接受时间、case04先valid等待ready、case05输入输出同拍，分别spec通过且事务关系PASS。不要求ready/valid逐拍同形。case04和05只承诺固定共同ready/单笔场景，不是所有独立ready组合下的通用组合广播实现。
- 因果破坏：case06最终flat都是[[81,1]]，但RTL两sink在cycle3已收、source到cycle7才接受。账检出2UNEXPECTED_TRANSACTION及最终2MISSING_TRANSACTION，意图FUNCTION_FAIL；早输出不抵扣将来输入。
- reset：case07 reset前接受(0,0)，sink0已交付；8拍取消sink1 pending[0,1]与两笔未接受offer，既有交付保留。8/9 reset行无语义握手，下epoch用新id。case08旧pending跨epoch，cycle10向sink1交付旧[17,0]，新输入cycle11才接受，UNEXPECTED_TRANSACTION及意图失败；新校准不重复旧v2错误类别过窄的预声明。
- 不可对齐：case09 IR reset前只接受一笔，RTL双槽接受两笔；两者spec各PASS，但pending取消分别[0,1]/[0,2]、未接受分别2/1，意图NOT_EVALUABLE。没有移动固定8/9 reset或删掉不利事务。
- 环境/采样负例：case11外部源在cycle6将受背压的[18,0]改为[19,0]，两边INPUT_PROTOCOL_FAIL，不算DUT命中；case12原raw160事件完整，只按预声明在评估view删PRE6（79行），报告TRACE_INVALID/NOT_EVALUABLE。全raw单独只读账无功能错误，删样不是RTL破坏，不改原文件。

同作者另写audit_evidence.py只读取已有raw/receipt，按平面接受历史+消费计数重算counts/accepted/delivered/aborted，核全部源、旧20354绑定、run270绑定、raw-normalized逐字段、IR打包输出与同构320相位事件。未import目标checker/relation/IR，没有再执行工具。结果PASS_READ_ONLY_EVIDENCE_HASH_AND_TEMPORAL_ACCOUNTING；这是自检，不替代总控独立审核，也没有执行第三个独立作者参考。

## IR映射及局限

至少一份当前R6语言完整3寄存器broadcast JSON确实被原parse解析，并经新增yield的run_stream解释；task overlay仅在新隔离进程，原R6 intent/tasks/runner不改。对这一锁定人工映射，同构RTL/手算和不同事务时序提供有限实测证据。没有验证所有IR表达式、16寄存器边界、任意队列/时钟/复位域，也没有证明流式插桩与未插桩batch run在所有输入下运行时等价。

插桩是从锁定run AST末尾last更新之后增加yield，不扩IR语法；本批没有另行重放原run，不能把“单点AST变换”说成形式等价证明。当前harness是独立开发适配器，不是R6原生产逐事件全端口等式已经变成事务对齐。S三路关系仅描述可见关联，不推模型内部理解原因；D无IR不能推阶段。原默认回归未重试，工具exe SHA绑定不覆盖全部传递依赖，Icarus/vvp可读版本仍UNKNOWN；80拍/公平drain不证明无界活性、异步物理释放、完整AXI或glitch。

## 原证据保全与后续条件建议

阶段A24源/plan/plan-lock/PREPARATION保持原字节；其“未执行”是准备时历史状态，当前执行事实以本报告及run summary为准，未回写准备封存。v2 packet c614a325...、设计补正090fa59f...、R7封存、原v2 15/16完整条件/exit1与旧默认24tests/3fail/1error/2skip/exit1全保持。run270证据绑定与末次只读自检通过，另以execution-bindings/report packet封存当前材料。根计划/GUI共同模块/学校任务不动，自动化fyp仍暂停。

建议结论：**在总控独立核验本批原证据通过之后，有条件具备另行准备有限新外部任务来源与契约盘点的测量基础**：已经实测本映射PRE/POST相位、合法时间差异、因果违规与reset集合不可比处理。此结论只支持“准备方案”的下一关，不授权现在检索/扩候选，不等于冻结外部最终集、S/D×F/R自然模型批或生产接入。

下一关仍要明确未参与调优的新来源/独立参考、域和采样适配、规格可比性、split及调用机会预算、私有反馈隔离与新精确SHA。人工开发命中没有提供自然模型收益或阶段定位效用估计。本轮按授权完成即停，只向总控回传一次，不派生新准备轮或重跑任何场景。
