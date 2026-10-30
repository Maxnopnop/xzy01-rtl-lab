# 任务独立性、作者与手推见证

本轮三题由本探索助手按文字语义原创，均为开发题。旧R1/R2五家族rt_sequence/sticky_alarm/event_parity/request_delay/debounce3及R3四家族cancel_deadline/retrigger_window/elastic_slot/rotating_owner未重跑、未改名派生。基础寄存器/计数概念当然共用，不声称语义原语全新或与世界上所有题无近重复。

|新机制|关键可区分规则|与旧题/基础题的区别|
|---|---|---|
|epoch_commit|两银行隐藏staging；同边沿write参与原子commit；abort取消写入和commit；组合读取live|不是R3一槽消费替换或取消deadline，没有req/busy窗口；可缓存多个未提交银行，读不暴露staging|
|refund_credit|退款先饱和到5，再按权重消费；零cost拒绝；组合可支付预测|不是递增/递减单位计数或retrigger timer，不计算到期；同边沿交易包含饱和顺序及带权条件扣款|
|tagged_join|双流有标签缓存；新样本先替换再比较，匹配消费两侧、结果XOR；flush优先|不是FIFO次序、弹性ready/valid单槽或所有权仲裁；不匹配标签允许等待，替换旧标签会取消原潜在匹配|

固定全部输入二值行为，包括零cost、重复commit、同边沿新标签替换、复位/flush/abort优先级。无未定义非法输入，格式/不支持属于模型意图输出的状态，不能把规格边界当删样借口。

两参考作者都是本助手，同一自然语言规格，存在共同误读和同作者风险。过程oracle使用bank列表/dirty掩码、整数账本、可选(tag,data)元组；RTL独立写寄存器、next临时量和位运算。Python不读RTL/IR，RTL不从契约转换。人工契约另写来校准双格式解释器，仅人工机制证据；不能算第三份独立正确性证明或模型计划样本。手推见证不从IR自动计算，仍同作者，应由总控按文字复核。

|公共第一序列边沿(从0计)|手推后边沿 packed输出|理由|
|---|---|---|
|epoch_commit 0|2|只stage银行0=3，visible仍0、dirty01、无commit|
|epoch_commit 2|25|同边沿写银行1=2并提交，visible银行0=3，dirty00，committed1|
|epoch_commit 4|24|abort胜过write+commit，live银行0仍3、dirty00、pulse0|
|refund_credit 0|24|退款3，credit3，cost0预测不可支付，无submit脉冲|
|refund_credit 1|29|old3+refund3先饱和5再扣2=3；accepted1，当前组合仍可付|
|refund_credit 2|4|支付3后credit0、accepted1、can_pay0|
|tagged_join 2|5|新A(tag1,data3)替换oldA与B(tag1,data2)匹配，result1、joined1、pending00|
|tagged_join 3|7|同边沿两新tag0样本2 XOR1=3，joined1，pending00|
|tagged_join 第二序列1|24|新A tag1先替换旧tag0，B tag0不匹配，pending11、joined0、result0|

实际事件index/对应oracle值在calibration-v4/manual-witnesses.json。公开事件61/56/46，隐藏6625/4720/14290。隐藏包含手工公共序列、32条固定seed随机24边沿、每个packed输入的三边沿上下文及中途复位；账本另有预先定义的满额退款cost1边界。非全状态穷举、非无界证明，随机/手工覆盖仍可能漏检。

校准核心突变：commit使用旧staged、退款扣款使用旧credit、join使用旧缓存tag，公开/隐藏3/3检出。额外账本满额refund3/cost1错误公开PASS、隐藏FAIL；公开盲点冻结保留，不增公开例子。首次局部tb命名策略失败、JSON tuple/list比较失败及突变重引tb策略失败均保留于calibration-v1/v2/v3，最终v4完整通过；未改任何模型成绩。
