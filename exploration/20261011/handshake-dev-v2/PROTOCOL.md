# 有限预声明矩阵

顺序执行8配置，compile15s/sim10s；总准备3600s、新包250MiB软界。所有 native 80拍，末16拍消费者全ready，checker要求8拍公平尾。初始3拍reset；scene0中途8/9拍reset；scene1为8笔持续输入；scene2/3为单笔输入。

| 配置 | kind / scene / fault | 预期 |
|---|---|---|
| shared_reset_flush | 0/0/0 | PASS，已交付[1,0]，取消pending[0,1]、unaccepted2 |
| shared_reset_stale | 0/0/1 | FUNCTION_FAIL，DATA_OR_ORDER_FAIL |
| queue_reset_flush | 1/0/0 | PASS，已交付[2,0]，取消pending[0,2]、unaccepted1 |
| queue_reset_stale | 1/0/1 | FUNCTION_FAIL，DATA_OR_ORDER_FAIL |
| queue_continuous_independent | 1/1/0 | PASS，独立ready、8输入 |
| legal_same_edge | 2/2/0 | PASS，输入输出同拍 |
| legal_valid_before_accept | 3/3/0 | PASS，valid提前呈现，7拍同时接受 |
| illegal_consume_before_accept | 4/2/0 | FUNCTION_FAIL，UNEXPECTED_TRANSACTION；最终flat序列却相同 |

8手推见证：同拍、提前valid受背压、合法reset部分取消、合法不同消费者延迟均PASS；提前消费、reset后旧输出、reset释放旧valid、stall释放换载荷均FUNCTION_FAIL。它们是新增边界，不重跑v1的22/10。

6设计语义例：时间差异匹配、IR错RTL对、IR对RTL错、共同错、reset接受集合无法对齐、旧IR表达域不足。仅 DESIGN_ONLY 示例，不运行新IR解释器，不声称IR/RTL集成已验证。

预锁 v1 prior全部20065绑定、新v1完整包及封存元数据、R7包（由旧绑定覆盖）、fsm_ir.py和仓库3项默认测试源；新run锁其实际源。check复制不改，生产runner/FSM不修改，所以仅复用原默认回归负回执，不重复调用AGENTS规定的生产runner回归（若发生实质生产runner/FSM改动才在新目录执行一次）。结束冻结、交总控，不自动进入外部保留任务。
