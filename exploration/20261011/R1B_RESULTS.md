# R1b有限补强交付（2026-10-11）

结论：**已校准SAT的正例、界限、反例和语法错误状态，独立过程参考支持这五题；24份历史真实模型RTL中，7份原失败在14/32步均有反例且独立Icarus重放成功，17份原通过在这两个界限内均无反例。本轮未发现原PASS上的新增错误。** 这说明当前补强可重复发现已知错误，尚未显示对这17份原PASS的增量价值，也没有方法生成效果证据。

目录根`E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261011/`。以下相对路径均在此目录。首轮脚本/协议/四run/RESULTS/verification冻结，学校记录与原RTL/成绩未改变。本轮新增：[预声明协议](R1B_PROTOCOL.md)、[版本修正](R1B_AMENDMENT.md)、[精确勘误](R1B_ERRATA.md)、[最终源码](r1b_v2.py)、[最终run汇总](runs/r1b-v2/summary.json)、[独立核验](r1b-verification.json)。

## 校准：真实工具证据与模拟状态测试分开

|真实校准|次数|预期与实际|
|---|---:|---|
|五题正确fixture vs独立过程RTL参考，14步|5|NO_COUNTEREXAMPLE_WITHIN_BOUND|
|rt_sequence语义等价的状态重命名，14步|1|NO_COUNTEREXAMPLE_WITHIN_BOUND|
|同一12位延迟克隆，12步|1|NO_COUNTEREXAMPLE_WITHIN_BOUND|
|同一12位延迟克隆，14步|1|COUNTEREXAMPLE_FOUND|
|损坏Verilog语法，真实Yosys前端|1|SYNTAX_ERROR，未进入SAT|

全部9格符合预声明状态。[calibration.json](runs/r1b-v2/calibration.json)逐格记录、日志和miter保留。五个独立手写过程参考先经真实Icarus旧固定TB全部通过：[references.json](runs/r1b-v2/references.json)。rt_sequence参考用4bit历史寄存器，sticky_alarm用前一位和锁存，event_parity用异或，request_delay用阶段，debounce3用连续相反输入计数；不由fixture_rtl生成。仍是本任务人工实现、固定测试核对，不冒充外部审核。

另外8个解析器输入测试及1个mock缺失可执行文件测试核对TIMEOUT、OUTPUT_LIMIT、UNSUPPORTED、SYNTAX_ERROR、TOOL_ERROR、UNPARSED_TOOL_RESULT、无反例、反例、ENV_ERROR。它们只验证分类路径；本轮历史样本没有实际timeout/unsupported/environment错误，不能把mock计入真实EDA证据。检查器不再将未知输出或工具失败当作无反例。

## 历史样本与负结果

新增SAT结果生成前冻结[selection.json](runs/r1b-v2/selection.json)。纳入所有支持题的7份原FUNCTION_FAIL，再按task/model选择PASS并轮转补到24；原结果/DUT SHA256完整绑定。来自FSM48与paired-A/B，sol9、terra15，17PASS/7FAIL，23个不同RTL字节hash。一个重复簇保留，不当作独立题。ve_fsm12个结果因本版本无独立过程参考未纳入，另2TIMEOUT无RTL排除，均记录原因。

|题族|原PASS|原FUNCTION_FAIL|14/32步新增结果|
|---|---:|---:|---|
|rt_sequence|3|4|3份两界限无反例；4份两界限有反例|
|request_delay|4|3|4份两界限无反例；3份两界限有反例|
|debounce3|4|0|4份两界限无反例|
|event_parity|4|0|4份两界限无反例|
|sticky_alarm|2|0|2份两界限无反例|

48项SAT状态：34个NO_COUNTEREXAMPLE_WITHIN_BOUND、14个COUNTEREXAMPLE_FOUND；0新增原PASS反例。14条solver轨迹全部生成独立Python过程oracle期望，用原字节DUT在Icarus重放，14/14 FUNCTION_FAIL：[history-results.json](runs/r1b-v2/history-results.json)。这是7份原失败在两界限的重现，不是14个自然失败，更不是7种独立错误机制。

代表例子：选择index0原FSM/prose/terra序列失败，SAT给出`01001001`，独立oracle末端应检测重叠1001，Icarus见证18次检查中1处不一致；index4–6原paired/terra延迟错误，14步反例为`0001`，接受请求当拍应q=0，见证检出提前输出。完整原路径、hash、输入和预期保留于核验文件details及各history/<index_task>/<bound>/witness，不声称这些SAT见证最短。

## 证明域与限制

- Yosys0.52、read_verilog -sv、proc/flatten/opt/async2sync后内建SAT；set-init-zero，rst_n只在step1为0，其余为1。给定界限只约束这个初始化和复位序列。
- 每一步是抽象posedge tick。输出state对应上一时刻输入；12位前缀位在step2..13，到step14才观测失配。因此12步无反例是明确的界限不足对照，不是正确性证明。
- 不覆盖中途reset、边沿间异步断言/释放、任意初值、recovery/removal、CDC、多时钟、Mealy域。async2sync本身带建模假设，不能拿其结果声明物理复位行为正确。
- 手写RTL过程参考减少共用转换器风险；独立Python过程oracle/Icarus复现实测支持反例可靠性，但不构成完全独立外部参考审计。
- 同五开发题、偏向保留原失败的样本选择、每题多个重复输出，因此不估计总体错误率、不做自然错误频率或统计显著性主张。17个有限界限无反例并不证明固定测试无遗漏。

## 字节绑定问题及实际成本

首版r1b-v1记录的original_sha256对read_text换行规范化后的字符串计算，24个字段均不匹配原DUT hash。更精确的字节审计确认：Windows write_text转换回来后，24个original.sv实际字节均与源相同。执行前amendment曾推断实际复制字节也不同，已用独立[R1B_ERRATA.md](R1B_ERRATA.md)纠正，未改冻结文件。最终v2改用read_bytes/decode与write_bytes；48项原字节/hash绑定及mapped仅module声明改名全部通过。v1/v2选择清单和SAT状态完全相同。

v1和v2各57个Yosys检查命令（56项进入SAT、1项语法前端失败）、19次Icarus评估；实际本轮合计**114个检查命令、112次SAT、38次Icarus评估**，另2次Yosys版本探测。v1约16.515s、v2约14.485s，独立核验约2.4s；重跑成本没有隐藏或当成新增模型样本。最终run约1.8MB，低于100MB声明预算。CPU顺序1、Yosys30s超时、compile15s/sim10s，无新增模型调用、token或付费服务；本机离线费用字段0不估算电费，首轮4次服务失败的费用仍UNKNOWN。

独立核验六run锁：首轮1612文件完全不变，r1b-v1/v2各682文件及source locks通过。首轮verification没有重写；新版核验单独保存。所有24原result/DUT未改，源码快照仅新增snapshots/r1b-v2/。

## 主张—证据—局限—下一实验

|主张|证据|局限|下一项最小实验|
|---|---|---|---|
|状态分类在当前工具版本可靠|9真实校准格+9单独模拟解析/适配测试|真实timeout/unsupported未触发，只有路径测试|遇新的结构或工具版本时先新增该类型真实校准，不自动当无反例|
|在支持域内重现自然模型已知错误|7历史RTL、两界限共14反例，独立Icarus14/14复现|集中terra两题；同错误/重复输出非独立机制|新开发题族冻结后按行为深度/复位风险选择有限自然输出，不仅加同构夹具|
|对这17原PASS尚无增量发现|两界限34项无反例，所有分母保留|32步、固定reset/初始化，不能无界推论|优先加入中途reset与边沿间仿真契约；通过校准后再谈无界或更深SAT|
|E4说明故障模型和有限评分边界|一个前缀克隆机制在五开发题上绕过评分|人工对抗实例，非5种自然失败、非LLM过拟合频率；漏检本身非独立新颖性|作为校准和论文限制保留，不再大量复制同类夹具|
|模型效果比较未验证|首轮4API_ERROR、R1b无新调用|gpt-6.1-sol仅本地配置值，不能证明可用|有服务/身份/路由变化后才新run探测，不静默替换冻结gpt-5.6-sol方案|

一次只读[routing diagnosis](r1b-routing-diagnosis.json)：ChatGPT已登录，本地默认配置模型gpt-6.1-sol、默认OpenAI供应商，无自定义provider、无启用CSV端点，HTTP/HTTPS/ALL_PROXY环境变量均不存在。未读认证secret、未网络刷新模型列表或重新exec、未改VPN/路由。没有可确认可用的替代端点，因此服务问题仍阻塞真实生成比较；配置的模型名不等于服务可用性。

本轮明确结束点已达到：校准通过、24份附加验证完成、反例复现、旧锁只读通过、报告交付。没有扩大样本、新建轮询/对话、向总控自动发消息或自动关机。

复核命令（仓库根）：

```powershell
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' exploration/20261011/r1b_verify.py
```

仅更新本目录r1b-verification与新增快照，不修改冻结首轮核验。已执行r1b.py/r1b_v2.py拒绝覆盖对应run；需要新版本时使用新源码/协议/run。
