# R4机制pilot结果：全首次通过固定检查，表示/反馈无可观察收益

按总控独立审阅后明确放行的SHA `dba616332a6fddd2d04d3def9b632b7fe0c2db8affb2bafe53ce7fdb9dfa87c6`执行一次有限批次。原runner_v2未修改，3新族×2重复，48唯一调用全生成/评分/封存，0未启动/未知/API失败/重试/补样。完成即停，不扩大轮次。

12真实模型意图均解析受支持且对固定独立参考PASS；12首次RTL均PASS。24最终RTL各策略6/6，三向关系36个RTL均ALL_MATCH。不存在自然语义失败或表示/RTL分歧实例，因此不能估计修复收益、证明内部理解/编码错误定位能力，不能将全PASS当结构表示或执行反馈的优势。

## 全分母主结果

|策略|计划固定分母|最终RTL_spec PASS|RTL_intent PASS|未启动/未知/格式/域外失败|
|---|---:|---:|---:|---:|
|JSON+重新生成|6|6|6|0|
|JSON+执行反馈|6|6|6|0|
|受控线性+重新生成|6|6|6|0|
|受控线性+执行反馈|6|6|6|0|

意图：JSON6/6、受控线性6/6；首次RTL：JSON6/6、受控线性6/6。首次结果全部保留，没有按成绩、长度、格式择样。本批IR_INVALID/EXTRACTION_ERROR/UNSUPPORTED/INPUT_LIMIT/COMPILE_FAIL/FUNCTION_FAIL、API_ERROR、UNKNOWN_INTERRUPTED、PENDING皆0；这些路径的离线校准不混进研究分母。

|新族|JSON反馈vs重新生成（2对）|线性反馈vs重新生成（2对）|
|---|---|---|
|epoch_commit|help0/harm0/no_change2/inconclusive0|help0/harm0/no_change2/inconclusive0|
|refund_credit|help0/harm0/no_change2/inconclusive0|help0/harm0/no_change2/inconclusive0|
|tagged_join|help0/harm0/no_change2/inconclusive0|help0/harm0/no_change2/inconclusive0|

合计12反馈对：help0/harm0/no_change12/inconclusive0。每个反馈条件下JSON/线性6对的PASS状态也全相同。可解析IR敏感性子集恰好等于主集，每策略仍6/6；没有证据支持正或负处理效应，也不能从这6开发例推出一般无效/统计等价。

## 三向判据与定位范围

原results.json保留12意图IR_spec和36个RTL的IR_spec/RTL_spec/RTL_intent，均PASS；96真实编译/仿真覆盖12个首次的24公开检查及36个RTL的72隐藏检查。意图期望由该槽真实模型原文经受限解释器计算，没有人工正确契约替换，人工契约只留在前期校准。

观察分类ALL_MATCH36，BOTH_DIVERGE/INTENT_DIVERGES_RTL_MATCHES_INTENT/CORRECT_RTL_DIFFERENT_INTENT/RTL_DIFFERENT_INTENT/NOT_ASSESSABLE皆0。此批只验证三路记录可绑定且在这些事件一致，没有真实分歧见证，不能验证各异常类别对模型内部错误的归因准确度。最终两臂只改RTL、不改意图，不存在意图修复率。

主因素是JSON分节与同域受控线性意图的组织形式；两者均受限制，不是有结构vs无结构/自由散文。每策略三阶段机会，不能回答结构化状态表整体优越性或严格等算力效果。重新生成拿到相同规格/例子/真实意图/候选/指令，只有执行反馈增量缺失；其6/6表现构成强基线，本批增加反馈没有带来可测增益。

## 实际调用与费用账

实际唯一调用48=12意图+12首次RTL+24最终RTL；四策略各18机会（全共享口径和72不能当实际次数），半共享分摊各12，合计48。全部请求同gpt-5.6-sol/low；仅确认请求配置和实际CLI回执，server模型snapshot未暴露。

|阶段|唯一调用|input|output|cached input|cache write|reasoning output|
|---|---:|---:|---:|---:|---:|---:|
|意图|12|128686|9498|81664|0|5056|
|首次RTL|12|133662|6421|74240|0|140|
|最终RTL|24|282258|12760|144000|0|279|
|唯一实际总账|48|544606|28679|299904|0|5475|

下表是各表示共享前两阶段一半+自己最终调用的实际分摊；cache write均0。小数来自会计分摊，不代表服务返还半个token。

|策略|分摊调用|input|output|cached input|reasoning output|
|---|---:|---:|---:|---:|---:|
|JSON重新生成|12|135417|6829|81664|1165.5|
|JSON反馈|12|136149|6877|74240|1165.5|
|线性重新生成|12|136154|7651.5|73472|1711.5|
|线性反馈|12|136886|7321.5|70528|1432.5|

完整部署视角各含全共享的input/output分别200869/10603、201601/10651、201876/11837、202608/11507，其他原字段及逐槽/共享/分支账见actual-analysis.json.actual_ledger。该口径重复计算共享产物，禁止求和作实际消耗。

费用金额UNKNOWN，没有账户账单或价格结算证据，不将UNKNOWN当0。上述CLI原usage字段分别列示，不再把缓存/推理字段额外加到input/output。输出长度/缓存/推理量实际不相同，没有强制服务token上限；匹配调用机会不等于严格等token/算力。本批token差异仅描述性成本数据，不能因同样全PASS就声称某表示一般更高效。

预声明的token效率敏感性见token-sensitivity.json：每1000分摊output token的PASS数按表中策略顺序为0.8786/0.8725/0.7842/0.8195。它们来自同样6个PASS和不同生成长度，只作描述，不替代固定6分母或支持等token因果排名。

模型exec合计723.469s，含adapter预检查合计748.667s；从派发起到原评分文件完成804.927s。封存run约6762767字节；未触发180s单exec、10800s派发、750MiB派发前阈值或256KiB输入限制。时间、token、模型输出长度不同不据此删样。

## 生产运输与独立证据

前4实际服务gate通过，gate-audit.json绑定实际版本/请求/完整prompt/事件/输出/usage/无工具边界，功能成功不从gate推出。全48CLI回执都为codex-cli 0.162.0-alpha.17.2，同exe SHA `d13914ced6c7af174d8d638db938284231227312104b06a25e9608c632a7daec`，48独立thread id，工具item未出现。实际prompt范围2901..8341 UTF8字节；stdin路径在这些真实请求中成功往返，不证明256KiB或任意更长context接受/截断行为。

cli-turn-count-audit.json逐日志确认48次CLI invocation各只有1个turn.completed，合计48；次数和无重试主张指冻结槽/CLI回合层，不推断未暴露的provider内部行为。

actual-analysis.json独立核验PASS：34来源、2480封存文件、48精确prompt/原响应/完整CLI事件与usage、96编译/nonce仿真、616544事件向量逐行绑定、真实意图对私有参考纯解释器比较、四策略/共享账与原summary完全一致，8066旧材料绑定不变。原始证据在runs/prepared-v2；分析位于run外，未改原评分/判据/源码，没有追加模型调用或重判RTL。

## 负结果、限制与停止点

首次全部正确再次造成天花板，比R3增加真实中间意图和新的时序语义机制并未获得自然错误样本。研究负结果应保留：本批无法识别表示/反馈修复收益或用真实分歧检验定位类别。支持的是此小域的流程可行性与固定测试一致性，不能把工程补强当研究贡献。

任务仅3原创开发机制，2重复/族并非独立任务；两参考同作者/同文字规格，有限二值/settled事件覆盖，非最终集/无界证明。公开账本blindspot、calibration-v1/v2/v3失败、默认代理34回归3failures/1error/2skip原样保留，不报全回归PASS。本批没有实际域外/格式失败，不能用主结果替代这些路径的离线验收。未做综合/PPA；后代进程树清理仍未独立验收。

已有ASTF/分阶段反馈近邻与论文范围在LITERATURE.md；不称首次提出，也不横比论文通过率。下一步是总控只读核查本批研究价值；没有下一执行轮。若将来另行设计能区分自然时序错误的最终集或明确假设，须新任务/参考/预算/审核，不在本批看到天花板后加题、造错混分母或扩样。
