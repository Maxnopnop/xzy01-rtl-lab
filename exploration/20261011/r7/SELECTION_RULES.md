# 有界来源候选规则（检索前预声明）

候选总分母最多12，不按模型成绩替换/补满：

1. alexforencich/verilog-axis：axis_cobs_decode
2. 同库：axis_cobs_encode
3. 同库：axis_frame_join
4. 同库：axis_frame_length_adjust
5. 同库：axis_stat_counter
6. 同库：axis_broadcast
7. 同库：axis_tap
8. 同库：axis_async_fifo
9. pulp-platform/common_cells：serial_deglitch
10. 同库：edge_propagator_ack
11. 同库：fifo_v3
12. 同库：rr_arb_tree

以上是来源定位候选，不代表纳入；路径不存在/不可访问也占检索分母，记录负结果不无限换源。README、许可、依赖是原来源核验资料，不作为新增题候选。最多2仓库固定revision；下载仅必要文本源码/规格/许可，单文件≤512KiB、总原来源≤8MiB、最多64个必要文件，不下载大权重/仓库大包。HTTP403不重复同失败请求，来源无法核对即记录不可执行。请求和检索结果保存访问记录。

目标机制：流的编码/长度边界与时序、广播消费者独立背压/逐消费者接收、输入稳定资格/抑制毛刺等跨拍OLD/new-state规则。目标错误是自然IR_spec、RTL_spec、RTL_intent的可见分歧；不为得到失败改规格、隐藏集或方法。

纳入需同时具备：(a)外部原始文字规则/作者或官方实现可读、版本/许可/原字节hash可核；(b)外部ref不是本项目作者或未审计LLM生成golden，原规则/ref依赖可描述；(c)此前项目未使用、不是R1–R6/Dev10/FSM/paired的端口/位宽/seed近重复；(d)现有R6固定IR支持域有可执行表达方式，不改域/提示/算法适配难题；(e)有确定可观察binary行为与有限Icarus可执行基线，不依赖未明确X/模拟CDC或隐藏环境；(f)只必要接口/参数适配，保留diff与原未适配基线，不静默修正ref。

先按以上规则排除不可执行/重叠候选，再按预声明排序与机制多样性取最多3机制：同一编码机制encode/decode最多1题、同一FIFO/arbiter近重复不纳入；优先不同规则机制，其内按清单序号。一般3机制×2重复=6case/48调用，只有可靠外部参考达到该数量才冻结；不足不强凑满。重复是同题LLM重复，不是独立新任务；训练污染未知。

冻结前0模型；只能核规格/ref正确性、可执行性、手推见证/时序判据，不用自然候选输出/隐藏成绩筛样。若为了候选改方法则该题降adapted-development、另记录，不冒称保留。本轮始终叫candidate-heldout，不预称已独立final test set。
