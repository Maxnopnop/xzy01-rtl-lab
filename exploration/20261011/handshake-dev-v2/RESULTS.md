# development-v2 有限离线交付（待总控独立审核）

## 实际完成与负结果

一次校准，8手推=4PASS/4FUNCTION_FAIL；8 Icarus配置=5PASS/3FUNCTION_FAIL；实际8编译、8仿真退出0，640拍raw与normalized。0模型、0来源检索、0候选扩充、0生产接入、0旧评分重判。checker.py与v1逐字同SHA。人工RTL确实由Icarus执行；同作者开发不等于历史真实模型或独立作者参考。

校准整体 **exit1 / all_expected=false**：shared_reset_stale的FUNCTION_FAIL符合预期，但预声明DATA_OR_ORDER_FAIL未出现，实际为1次UNEXPECTED_TRANSACTION。cycle10旧[17,0]交付consumer1，此时新episode第1输入[161,0]到cycle11才接受，故没有输入可匹配，应为意外事务。这是原预期错误类别过窄，未发现checker漏检；预声明、源码、原verdict/receipt/summary全保留，不改期望、不补run、不重试。native状态8/8匹配、类别条件7/8匹配；手推8/8匹配；合计状态16/16但完整预声明条件15/16，不能称“全校准PASS”。没有使用允许的修复额度。

## 有区分力的见证

合法shared reset：source cycle3接受[17,0]，consumer0 cycle4收，consumer1一直背压；cycle8 reset取消pending[0,1]及unaccepted2，原已交付保留。cycle8/9原信号保存但不计握手；下一epoch只交付[a1,a2,a3]。合法queue reset：source3/4接受两笔，consumer0在4/5收到两笔，reset取消pending[0,2]及unaccepted1；新epoch不泄露旧数据。两实现reset前接受集合不同，但按同一规格都PASS，不能以跨实现最终flat不相同判其错误。

共享缓冲残留cycle10为UNEXPECTED_TRANSACTION；独立queue未清空cycle10/11旧输出对应新接受载荷，产生DATA_OR_ORDER_FAIL。两故障均检出。FAULT只改变同步reset清空逻辑，原人工错误与原始轨迹不改。

双消费者独立深度2环形队列与one-slot共享pending结构不同；连续8笔、消费者ready不同日程下PASS。它独立读写指针/count，生产广播仍需两个队列都有容量。有限见证不证明所有队列边界或任意背压组合。

同拍传播scene2 PASS。提前valid scene3在3..6拍source ready=0且两个consumer ready=0，均保持[81,1]；第7拍输入输出同时握手，PASS。该组合DUT只在固定共同ready场景合法，不是任意独立消费者ready下的通用实现，不能跨场景推广。

提前消费故障：consumer0/1在cycle3收[81,1]，source到cycle7才收；最终各方flat序列都[[81,1]]。checker检出2次UNEXPECTED_TRANSACTION和最终2个MISSING_TRANSACTION（早输出不抵扣未来接受），阻止时间消去掩盖因果错误。在线账与另写索引计数审计同结果。同拍输入先入账再输出仍允许，未把提前valid当提前消费。

## 设计、保全与尚未证明部分

INTENT_COMPARISON_DESIGN.md与6个明确DESIGN_ONLY语义例完成。旧fsm_ir.py仅1bit Moore，不能表示本事务域。比较设计处理同外部驱动策略但不同接受时间、offer_id身份、reset接受/取消集合不一致、允许stuttering以及NOT_EVALUABLE。没有新IR执行器/三路分类算法/生产集成，不能称IR／RTL意图比较已验证。S可见关系不证明内部认知因果；D无IR不推理解阶段，私有意图诊断不额外反馈给F。

旧证据20231绑定均核验，包括旧prior20065、v1完整包与封存、R7旧封存、旧IR及默认测试源。v1 packet SHA仍d060a32dba45329046e7a71cf5b3c687fccc874bbaede47415bad3d3c9de268a；R7包SHA仍b2f63e5db433bc0a099574b65ecfffec30c787141741b11b3cb0126414cf506e。开发影响的R7材料仍是development，未新判候选/分数。

默认回归原负回执保持：24tests/3failures/1error/2skips/exit1。v2没有改生产runner/FSM/旧checker，未重复原默认回归，未改变代理环境或隔离重试；原失败不能称根因已证明是代理。新增校准本身exit1负结果另记。新审计只读取原轨迹/receipt，不import checker、执行编译仿真或调用模型；作者仍相同，不冒充外部独立审核。

有界80拍/公平尾、单时钟同步reset；不覆盖异步释放、采样间glitch、无界合法延迟/活性、完整AXI、自然LLM错误定位效用。最终旧绑定/原raw/源码/run/精确新包seal见seal-verification.json；总控审查完成前不自动扩批、外部保留任务或生产接入。
