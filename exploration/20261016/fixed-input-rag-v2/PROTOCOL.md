# 固定输入：RAG / 无RAG 统一有限方案

2026-10-16。状态 PREPARED / BLOCKED，0模型、0embedding/rerank、0正式编译/仿真/SAT。本方案替代单条件30槽位提案，唯一待审分母是5题×3模型×2条件×2样本=60，不是90。收到总控对精确计划的审核仍不自动消除下列阻断；目前没有可执行调度器。

## 原题与输入

task-manifest.json绑定同级fixed-input-direct-rtl-v1中原始资产。rt_sequence是已有paired-v1/dev10开发版本，原规格本来就带异步低有效复位、重叠检测及Moore输出澄清；不冒称原版RTLLM、外部holdout。其余sticky_alarm/event_parity/request_delay/debounce3是项目开发题。原规格字符串、接口、TB、向量、参考、原事件JSON和bin均不改字节。模型只见原spec与统一系统输出格式；未把manifest的示例、端口附带examples或public_contract额外加入提示词。

request_delay的“accepting edge保持0、following clock cycle”措辞可能引出周期解释歧义；原参考phase0→1→2(q=1)→3保持。保留该题与全部槽位、注明歧义，不借RAG补写任务要求，不把该歧义所致差异直接算理解能力证据；后续需总控决定是否允许按原检查器执行并分列解释受限项。五题都不是唯一RTL实现要求，静态审查也不能证明规格完全无歧义。

## 两条件及资料冻结

无RAG：原spec+既有统一输出格式，一次调用直接RTL。有RAG：同一spec/格式，user消息尾部只增加固定通用参考容器、出处/许可与逐字片段；无前置计划/IR、候选答案、反馈或私有测试。所有模型/样本复用同题同条件同一个messages.json，模型ID只在请求路由字段，不进入消息。requests中文件是拟发送JSON，actual_sent_prompts=0；不能将其称为已捕获的服务完整实际输入。

有效资料库是release/下的18段、1个公开来源；原corpus/的19段首版因过滤器漏参考式链接失败，保留负结果，绝不混用。来源lowRISC/style-guides，commit 9c15ff5dce23eef969e00ab3715153967419eadd，CC BY 4.0。原文/许可/访问回执及段落行号与hash齐全，保留署名和选择说明。它是项目风格指南，非语言标准；原题优先，不能添加题目接口或时序要求。

按预声明六类通用章节提取非代码段落；最多40段，80..900字符，文档顺序；排除代码、题名、解答、外链及依赖具体示例的文字。检索器retrieval_v2.py仅词法BM25(k1=1.2,b=0.75)，查询仅原spec、固定停用词、唯一query terms，无模型/embedding/扩词/重排。top-k=3正分，分数相同按ID；无命中为空，无补源；本轮request_delay只有2命中，照实保留。每题一次冻结结果用于所有模型样本，不按模型检索。重算只作离线一致性验收，不改变结果。

资料选择受开发题知识影响；旧OpenTitan阅读来自同一lowRISC生态，不能标成未调优/未见。contamination-audit.json比较全部paired-v1 spec及evidence/**/dut.sv共524路径（hash去重），五词窗口/原文/题名排查和手工通用性审阅；没有精确段落或题名命中。词法为0不是语义无重复证明，模型训练污染UNKNOWN。原全文虽含泛用代码，模型上下文只获冻结prose段落。

## 有限预算与公平性

固定gpt-5.6-luna、gpt-5.6-terra、gpt-5.6-sol。每模型每条件10槽位、每题2样本；每次拟共同max_completion_tokens=8192，总上限491520，每模型163840，每条件245760。并发1、一次请求超时180s，模型阶段12000s、整批28800s，输出文本128KiB、HTTP响应1MiB。temperature/seed/reasoning_effort均不发送，必须先核实共同支持及默认行为，不能以省略参数证明等算力。实际input/output/reasoning/cache token、耗时、货币/账户用量分列，缺失为UNKNOWN。RAG额外1410..1650字节/字符，并不等于token；本机检索时间另列。

顺序在slots.json预声明轮转模型和两条件先后；样本序号/顺序不进入提示词。60槽位全部保留。预算为上限不是执行授权，无采购/充值。现有服务价格/账户费用未知，禁止无依据费用估算。失败不删除，不替补、不自动重试、不静默换模型；任一403/认证错误/模型不支持/传输异常/未知完成/包装偏差停止全部新调用。未知调用仍占一次机会，绝不重发。完整返回但无效RTL是样本结果，不因质量差停止或重抽。

## 同一RTL的原检查与增强检查

原始回复只保存一次；沿用原rtl_lab.extract_rtl规则，单代码块、128KiB等失败分类保持；保存原回复与提取后的精确字节hash。不人工修RTL或再次生成。每个有效提取样本同字节RTL分别做原固定TB、R1b14与32步、原R1c全事件。原固定测试FAIL不阻止增强检查；语法/结构不支持分别记录，不仅挑PASS。无可接受DUT则各检查填NOT_RUN_NO_VALID_RTL，仍留在60分母；受停止规则影响填NOT_STARTED/NOT_RUN_STOPPED。绝不以漏执行当PASS。

R1b：保留原手写过程gold与14/32步脚本，其set-init-zero、step1 rst_n=0后续=1、proc/flatten/opt/async2sync/opt全部不变。只把单文件编译拆为原reference.sv、原样dut.sv、miter.sv，并将wrapper实例gate A改为原任务模块名A；DUT无需改名。此静态适配须审核，不声称已实际验证。NO_COUNTEREXAMPLE_WITHIN_BOUND仅界限/初始化约束内无反例，非任意初值/异步释放/无界正确。COUNTEREXAMPLE_FOUND须独立Icarus见证重放才列可复现自然错误，重放失败保留未复现分类。最多120次Yosys，30s/次；最多120个SAT反例见证，各只重放一次，写入单独diagnostics，不回写任何原数据/提示词。不新跑校准。

R1c：逐字复制每题既有testbench.sv与events.bin，各90972事件，输入/复位/时钟同一事件赋值后#2比较，覆盖中途复位、release、low/high翻转、posedge/negedge保持。保留原相位及已知离散仿真限制，不换成新PRE/POST握手判据。统计新样本的错误相位与category；不修改原事件流或另加诊断流作为本批评分。原固定60+事件60+SAT见证最多120，共最多240次Icarus评测，编译15s/仿真10s。hash漂移立即停止，连续3个工具基础设施失败停止验证，未执行保留。无学校任务、综合/PPA或新候选。

## 数据隔离、记录和分析

生成进程只能收到对应请求消息和公开片段；不挂载原参考、TB、私有向量或历史答案，不启用工具/检索插件/项目上下文。评测阶段才能读取私有资产，且不把诊断回传生成端。只保存脱敏请求/响应、模型requested/returned身份、usage和阶段回执；不保存凭据到包或Git。

每槽独立generation、extraction、original_fixed、R1b14、R1b32、R1c、diagnostics字段，避免stage覆盖；所有类别以及费用不明保留。正式runner尚未实现/离线验收，不能直接调用旧main选择器，因为它们按历史结果筛选或校准。各检查成功/失败/不支持/超时/环境错误/未执行分别以完整60及各模型条件10为分母报告。

按模型列原检查与增强检查的通过/失败、原PASS新增可复现SAT/事件错误、负结果和错误类型。两条件按task/model/sample索引预声明配对，列错→对、对→错、均对、均错；服务失败/缺测单列，不偷算功能错误或删去。每模型条件10样本仅描述性，来自5开发题且训练污染未知；sample索引不是相同随机种子或潜在输出的反事实配对。不得宣称IR收益、推理阶段因果定位。仅两条件不能证明自动检索优于等长度固定上下文，额外输入token/通用指令效应未分离，不加第三臂。

## 执行阻断与审核门

1. CLI历史没有生成token硬上限，隐藏system/developer包装不可完整观察；不得用旧成功调用保证本次逐字一致。
2. 本地API CSV只有禁用占位配置与DEMO_NOT_REAL，未验证三个指定模型共同服务支持、硬token cap、默认参数、服务端额外包装与准确返回身份。无网络探测调用。
3. 当前Yosys仅有历史0.52版本记录；未核实本机现版本/二进制。Icarus/vvp二进制hash匹配原记录。
4. 新批次执行器与分阶段保留/预留账、请求捕获、原DUT无修改适配的实际运行未实现或验证。不能把静态模板当执行器已就绪。
5. request_delay措辞歧义已列，解释边界待总控审核；不修改题目解决。

本轮只准备文件/离线审查。总控应先审核精确packet和plan SHA，再决定是否另行补齐阻断；任何工具/传输/方案改动须新版本并重新冻结，旧包保留。无自动开跑、扩批、补样或恢复fyp自动化。
