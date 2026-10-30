# 独立于被测执行代码的手算预期

这是同作者按契约作的另一种推导，不调用IR evaluator、spec_checker或relation生成预期，不自称外部/盲独立作者。源A/B/C按metadata.episodes固定，以不可撤销的“收货凭证”记交付，reset切分账本，只销未兑现凭证及未下单offer。以人工列出的输入/输出时刻和集合判断，程序运行不能反过来改变本表。

1. case01共享槽：接受3/5/7，两个sink收4/6/8，id/payload相同，spec均PASS、关系PASS。逐相位表见SAMPLING_ALIGNMENT。
2. case02 IR同01；RTL加两拍不可见延迟，接受3/7/11，收6/10/14。无reset，最终三id相同、各输出晚于其输入，PASS/PASS/PASS，不比ready波形。
3. case03 IR交替接受3/5/7/.../17、交付4/6/.../18；独立双槽RTL连续接受3..10、交付4..11，共8笔(0,0..7)，完整有序且字段相同，PASS/PASS/PASS。队列结构与共享槽不同，本例不证明任意背压组合。
4. case04仅(0,0)=[81,1]，两sink到7才ready。IR在3接受、7交付；RTL在3..6提前valid但无输出握手，字段保持，7才接受并同拍交付，PASS/PASS/PASS。
5. case05 IR输入3、输出4；组合RTL输入输出都3，同拍合法，PASS/PASS/PASS。
6. case06 IR如05；故障RTL输出3、输入7。最后双方序列都是一笔[81,1]，但提前交付凭证没有合法输入，RTL FUNCTION_FAIL，关系FUNCTION_FAIL，所需类别UNEXPECTED_TRANSACTION；IR仍PASS。
7. case07两边共享槽：reset前接受(0,0)，sink0已收，sink1取消(0,0)，未接受(0,1)/(0,2)取消；新epoch接受10/12/14，两个sink交付11/13/15，PASS/PASS/PASS。reset行任何端口显示都不计握手。
8. case08 IR如07；RTL未清pending，在10向sink1交付已取消旧A，新的(1,0)到11才接受，故UNEXPECTED，spec FUNCTION_FAIL、意图FUNCTION_FAIL。新epoch其余接受11/13/15、交付12/14/16，不能消掉额外旧A。
9. case09 IR如07；RTL双槽reset前接受(0,0)@3/(0,1)@4、sink0在4/5收两笔，sink1取消两笔，未接受只(0,2)。IR只有一笔接受/取消且两笔未接受。双方分别PASS，接受及取消集合不同，关系NOT_EVALUABLE；不移动8/9 reset。新epochRTL接受10/11/12、收11/12/13。
10. case10复位取消策略未定义，预先SPEC_AMBIGUOUS/SPEC_AMBIGUOUS/NOT_EVALUABLE，不运行、不合并进已执行功能分母。
11. case11共享槽与07相同，但外部源offer(0,1)在cycle4..5被背压、cycle6载荷异或1（6/7保持改变值），先违背了source的稳定承诺，双方INPUT_PROTOCOL_FAIL，意图NOT_EVALUABLE；不能算DUT人工故障命中。
12. case12运行映射同01，原raw仍完整；预声明只在RTL评估view删PRE cycle6，令轨迹缺样，RTL TRACE_INVALID，IR PASS，关系NOT_EVALUABLE。这是采样适配负对照，不是RTL错误、不是新仿真或静默编辑raw。

人工预期轴汇总：IR=10PASS/1INPUT_PROTOCOL_FAIL/1SPEC_AMBIGUOUS；RTL=7PASS/2FUNCTION_FAIL/1INPUT_PROTOCOL_FAIL/1TRACE_INVALID/1SPEC_AMBIGUOUS；意图=6PASS/2FUNCTION_FAIL/4NOT_EVALUABLE。它们是预期，不是成绩。未执行的场景/中途停止未到场景，必须继续保留完整12分母和未启动原因，不能把没观察到的预期当观测。
