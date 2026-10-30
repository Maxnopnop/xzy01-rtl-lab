# 参考依赖与判据范围审计（只读历史）

审计读取R3/R4 tasks/judge/intent、R1b_v2及根fsm_checks；不重新仿真历史模型RTL、不更改旧判据或分数。

|路径|依赖与共源风险|可支持的结论|未覆盖|
|---|---|---|---|
|旧FSM规格→fsm_checks.reference_ir→fsm_ir.product_check|reference_ir有手写transition或suffix/prefix构造；与候选共享parse/product checker，不能统称全部由同一RTL转换器生成|固定IR域一致性|独立作者/独立规格理解|
|mutation_study→paired_bank.fixture_rtl(reference/candidate)|参考与突变均通过同一个fixture_rtl转换器，另外timed_vectors与过程oracle交叉检查|限定IR编辑候选敏感性|共享转换错误/自然模型一般错误率|
|R1b手写SV→Yosys miter→Icarus反例|参考手写但同作者；reset初始、有界14/32、async2sync|有界可观察反例|无界/全部复位事件|
|R3/R4文字→tasks.step/output→vectors.expected→judge|期望由同一过程oracle产生，资产锁只固定判据，不能证明文字理解正确|模型与冻结期望的有限差异|独立规格证明|
|R4手写SV↔过程oracle|实现路径不同，不经IR转换；同作者/同文字|两实现一致+目标突变敏感性|共误读、外部独立作者审阅|
|R4 intent interpreter→IR_spec/RTL_intent|安全AST与过程oracle不同，但共同binary事件、同reset解释；人工正确IR仅校准|三路观测差异|内部思考/唯一阶段归因|

|R4规则|区分见证/资产|覆盖与缺口|
|---|---|---|
|epoch写入后同拍提交，abort优先|public sequences[0]第0/2/4命令；tasks.py手设计，过程期望+SV|公开/隐藏已含；空提交脉冲亦含|
|epoch staging不影响live，组合read|write后未commit+read_slot切换|已含；staged在dirty=0时等于live的内部文字不可观察，不应由PASS声称|
|credit饱和先于扣款、零cost拒绝|public首refund3，再refund3/cost2；cost0|核心覆盖；full5/refund3/cost1突变公开PASS/隐藏FAIL，保留盲点|
|tag新样本替换后比较、消费valid|public不匹配后替换、双新样本、flush|覆盖；无valid时cached值保留不可观察|
|异步复位与hold|R4向量reset_edge、midreset、high_change|midreset低clk；仅同时反相所有input，不是逐input；高clk无边沿reset/release未独立覆盖|
|参数/长期/未知态|固定bank2bit/cap5/tag1bit，random24且第3次reset|最长连续后段约21有效边沿；packedinput枚举不等于state×input穷尽；无X/Z/模拟窄脉冲/#2前瞬态/PPA/无界证明|

R5更换机制与参考，不能把新校准结果回填旧成绩。新两路径仍同作者；第二推导采用事件积累/词法payload折叠/集合距离最小化，不经过IR转换，增加可检查的不同推导但没有外部独立作者审核。总控审核也不能自动称独立作者实验。

R1c timed_reset.py复位/保持事件期望来自paired_bank.oracle历史prefix，r1b_v2手写SV另路径校准。此前64原PASS均PASS负结果保留，本轮没有重新评价这些RTL。本次只读猜测preserved-before文件不存在已改用R4实际prior-bindings.json，不新增旧run文件。
