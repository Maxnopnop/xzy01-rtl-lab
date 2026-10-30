# 采样及意图关系冻结

## 低电平到post-edge的唯一顺序

每周期10ns：t=0将clk置0并只在低电平设置rst/source/consumer-ready；t=2组合稳定后保存PRE的source和sink所有valid/ready/字段；t=5升沿，DUT更新寄存器；t=7保存POST，之后才推进源cursor；t=10进入下一低电平setup。source字段是TB reg，在PRE至POST之间都保持，不随posedge的source cursor立即改变。无DUT ready→consumer-ready或source-valid组合反馈；consumer-ready只由固定scene/cycle决定，source只在周期之间由上一个PRE握手推进，避免组合环和TB/NBA竞争。初始化DUT寄存器和三个同步reset边沿明确。

当前R6 intent.py的run在每row更新边沿bank后评价outputs。IR适配每周期先送clk0输入row，next_falling为空，因此返回值是新低电平输入下、尚未posedge更新的组合输出，可作PRE；再送同输入clk1 row得到POST。解释器环境在寄存器next计算时是旧state，输出使用更新state；隐式rst_n给sync_low。resetPRE可见旧pending但忽略所有握手，POST执行同步清空。将posedge row返回的POST直接当PRE会造成一拍偏移，本方案明确禁止。

完整broadcast-ir.json是当前R6语言下3寄存器one-slot映射，不改语言。原R6 TASKS仅三题，本实验只在新IR子进程将tasks模块绑定为metadata.py的development_broadcast接口，不改原文件、资产或生产评分；source锁同时绑定原intent.py及新metadata/adapter。输入/输出顺序和掩码由metadata.py固定。此处完整JSON仅静态准备，不是已验证可执行映射。

## 整段API与逐拍驱动的显式插桩

旧run返回完整列表，无法直接向依赖ready的driver反馈。新ir_adapter.py加载**哈希锁定**当前R6模块，取其run AST，在循环内最后的last=row['clk']之后仅加一条yield value，函数改名run_stream；parse/evaluate、next状态与输出表达式不替换。Feed按需提供下一low/high row，每case一个完整generator执行，160事件/80周期，然后耗尽。插桩本身是被审查与被测对象，不能称“原run未改”或“语义等价已证”。阶段A仅AST核插入点，不import/parse/evaluate/运行原IR。阶段B仅case01与07另外比较同映射IR/RTL全部160个PRE/POST端口值，任何偏移使该case失败并停止，不把后边沿输出当握手判定。

本批不增加“原run离线再重放”的第二次IR执行，避免超过预声明调用机会；因此插桩与未插桩run的运行时等价没有直接执行证明。透明AST仅一处插入、源码锁和同映射RTL+手算提供有限证据，接受这种限制须由总控阶段A审阅决定。

## 逐行手算相位见证（不是运行结果）

case01：初态(data,last,pending)=(0,0,0)，源A=(0x11,0)、B=(0x12,0)、C=(0x13,1)，两个sink全ready。

| 周期/相位 | 当行输入 | pending | ready / valid[1:0] | 当边沿事务 |
|---|---|---:|---|---|
| 2 PRE/POST | reset | 0 | 1 / 00 | reset排除，无事务 |
| 3 PRE | A valid | 0 | 1 / 00 | 即将接受A，无输出 |
| 3 POST | A仍保持 | 3 | 0 / 11 | A已入缓冲；此POST不是输出握手 |
| 4 PRE | B valid | 3 | 0 / 11 | source不接受B；两sink交付A |
| 4 POST | B仍保持 | 0 | 1 / 00 | 仅清pending，data仍A |
| 5 PRE | B valid | 0 | 1 / 00 | 接受B |
| 5 POST | B仍保持 | 3 | 0 / 11 | data变B，尚无B交付 |
| 6 PRE/POST | C valid | 3→0 | 0→1 / 11→00 | 两sink交付B，C仍未接受 |
| 7 PRE/POST | C valid | 0→3 | 1→0 / 00→11 | 接受C |
| 8 PRE/POST | source无效 | 3→0 | 0→1 / 11→00 | 两sink交付C |

reset部分交付场景：3 PRE接受A；4 PRE consumer0收A、consumer1不ready，4 POST pending=2；5..7 pending2且B保持未接受；8 PRE rst低，旧valid虽可见但不计握手，取消consumer1的offer(0,0)、未接受(0,1)/(0,2)，consumer0既有交付留账；8 POST pending=0；9仍reset无新增取消；10 PRE接受新epoch(1,0)=0xa1。FAULT残留在10 PRE多输出旧A，直到11才接受新输入，预期UNEXPECTED，不重复v2中错误类别过窄的预声明。

## 事务域意图关系

先分别按本实现PRE轨迹判断spec，并记接受(id,payload,cycle)、每sink交付(id,payload,source_cycle,sink_cycle)、reset时各pending id及unaccepted id。匹配只从当时已接受队列取id，提前输出id=None，不能向未来借token。再比较双方接受id顺序及取消集合；相同则允许cycle不同、只比较每sink有序(id,payload,last)并要求各自因果/背压/有界完成。不同则NOT_EVALUABLE，附集合差异。输入协议失败、缺样、未知控制、spec含糊也使关系NOT_EVALUABLE；不把它们归入DUT失败。即使最终序列相同，任一方因果/背压违规都使关系FUNCTION_FAIL。

IR_spec/RTL_spec与意图关系是不同轴。case09两spec可PASS但关系不可评估。相同字段错误若双方行为一致，关系本身可一致但spec失败；本批未增加该例。S三路只能描述可见关系，不能推内部认知；D无IR不可猜理解阶段，未来F不能多获私有意图信息。当前无生产三路集成/外部参考验证，全部为有限开发比较准备。
