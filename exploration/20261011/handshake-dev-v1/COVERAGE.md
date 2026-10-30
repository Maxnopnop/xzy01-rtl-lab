# 有限验收覆盖与盲点

|要求|手推trace见证|真实RTL|结果及边界|
|---|---|---|---|
|合法延迟|legal_five_cycle_delay、zero_cycle_combinational、simultaneous_enqueue_and_dequeue|LATENCY0/3|通过，事务等同/逐拍可不同；非任意无限延迟|
|无效载荷|invalid_payload_changes/unknowns|INVALID_STYLE1/2|data/last在valid0改变、含X通过；控制/有效data的X仍不可评分|
|每consumer恰一次|独立stall、late_extra_duplicate|loss_final_consumer0/duplicate_consumer0|末项缺失或额外项检出；重复payload本身并非错误，按计划ordinal/字段比对|
|顺序/有效字段|ordered_beats_swapped、accepted_payload/last_corrupted|data_corrupt|检出；无法区分完全相同事务的物理身份，未宣称内部原因定位|
|背压保持|stalled_payload/last_changed/valid_withdrawn|MODE3/4/5|stall→下一采样（含ready变1）必须保持valid/fields，破坏检出|
|拒收/有界交付|never_accepts_source、accepted_but_beyond_horizon|MODE7|source计划未接受/已接受却未交付检出，不让空队列假通过|
|复位取消/污染|declared_reset_cancels_inflight、stale_output_after_reset|只有initial sync reset|取消与未接受计划数量显式记账；旧epoch错误消费检出，非native中途/异步reset证明|
|环境/采集错误|source_changes_while_stalled、unknown_valid_control、insufficient_fair_drain、missing_cycle|native traces均正常|分别INPUT_PROTOCOL_FAIL/TRACE_INVALID，未作功能分数|

队列匹配和backpressure约束同时使用，未只mask所有valid0差异。drain/readiness是外部输入前提；末8+采样都有consumer ready1，source保持已计划但未接受的valid。固定window不代表无界liveness，超window缺失是有界契约失败。source valid不依赖DUT ready，避免错误环境把背压变相消失。

局限：两个消费者共享one-slot人工实现和其参数故障；没有状态×输入穷尽/形式证明/持续高吞吐/无限重复帧/采样间glitch/第三消费者/动态路由/CDC、任意AXI侧带或上游官方test覆盖。synthetic32观测不是32独立设计；same-author不同抽象仍有共源风险。未校准故障不能因这批全匹配自动认定可检出。
