# 规则—见证—覆盖边界

以下original-test列仅静态阅读；只有标本机观测者实际运行。没有生成R7公开/隐藏模型资产，private/public列均未分派，不把source测试数当覆盖率。

|候选|原规则与原测试见证|本机观测|未覆盖/阻断|
|---|---|---|---|
|1 decode|COBS零分隔/255码/输出帧；原Python算法+recv帧，pause|无|非法码/早last所有交错、复位中断、invalid载荷、exact ready/latency未知|
|2 encode|编码零插入/255段；原encode算法+recv帧|无|256FIFO状态、缓冲满背压、reset边界；固定IR不适配|
|3 join|tag小端+顺序四帧；原四源recv断言|无|live tag逐拍、非0口先valid、busy/ready精确时序、中途复位无完整契约|
|4 adjust|min/max、pad/trunc、original/current length状态；原测试范围/前缀/flags|无|16bit wrap、dynamic config中帧改变、status背压、多拍reset/invalid输出未完整|
|5 counter|trigger dump/reset、byte/frame accounting；原struct帧解包|singlebeat last→byte1/frame0及4输出字节|与一般计帧文字未解；sim源码参数8bit，非默认完整；overflow/trigger同拍/中途reset无全覆盖|
|6 broadcast|每consumer恰一次、独立背压；原recv各帧|valid0载荷变化、一次valid广播、所有消费者stall保持、中途sync reset清valid但payload留存|异步消费者交错消费/满skid/所有reset时点未穷尽；inactive输出不属帧契约|
|7 tap|不影响原流、stall截断置tuser；原last-cycle-user断言|无|截断边界/帧间背压/复位hold，原缓冲位置不属独立文字全周期规则|
|8 asyncFIFO|跨时钟FIFO/overflow/pause/frame；原独立source/sink reset tests|无|CDC模拟物理/任意双时钟；固定单时钟IR无法保留|
|9 deglitch|Threshold enabled周期、restart采当前、clear、async low reset|无|与旧debounce3近族；宏优先级/disable保留历史/reset release需独立证明|
|10 edge ack|发脉冲、保持待ack、双域同步反馈|无|独立reset/时钟/脉冲合并，固定域阻断|
|11 fifo_v3|原ID不存在，cc_fifo只背景|无|原身份/原规格/原test未知；不补为另一题|
|12 arb tree|FairArb下下一个active、LockIn stall、ExtPrio限制|无|旧rotating_owner家族；非2幂树/clear/hold/连续gnt/公平活性未独立验证|

OLD/new-state、reset assert/release、稳定时钟/下降沿保持、优先级、连续事件、背压、边界只在相关规则明确时才可构造权威期望。当前没有公私模型向量/属性资产，不能说已满足这些覆盖。两TB使用无timescale的逻辑#2间隔，仅逻辑离散事件，不声明2ns或模拟物理复位。没有synthetic模型负例、隐藏自然输出或成绩筛选。
