# R5中断批次收尾：20已返回、1未知预约、27未启动

本批没有完成48调用实验。原桌面turn中断后，新cursor下总控要求仅收尾，禁止重发未知预约或补样。确认关联runner/CLI已不存在后，run外离线finalizer按冻结未知预约语义将第21个`escape_frame__r1__structured__regeneration`记为UNKNOWN_INTERRUPTED，保留前20个原响应/事件及27个PENDING。收尾0新模型、无重发/充值/换模型/扩批，没有修改冻结源码/计划/原日志或旧成绩。

授权计划仍为SHA `752be8b79f544a86f0961ab50e5a8645ea7d18132792670d9373e095fd295b4e`。dispatch为STOPPED_INFRASTRUCTURE，具体原因是未知预约/桌面turn中断；不能解释成模型功能失败，也不能称完成48样本实验。中断的精确时间及服务端第21次结果无法由现有文件确定。已返回20次有完整CLI记录且无错误事件；第21次只有started、精确输入、request及本地version/auth记录，无codex进程退出/完整事件、response或usage，不据缺失记录推断服务器未消耗。

## 结果与完整分母

|阶段|PASS|UNKNOWN_INTERRUPTED|PENDING|计划分母|
|---|---:|---:|---:|---:|
|S模型意图|3|0|3|6|
|S首次RTL|3|0|3|6|
|D首次RTL|3|0|3|6|
|D第二次无条件RTL|3|0|3|6|
|S最终重新生成R|2|1|3|6|
|S最终反馈F|2|0|4|6|
|D最终重新生成R|2|0|4|6|
|D最终反馈F|2|0|4|6|

合计20 PASS（3意图、17 RTL）、1 UNKNOWN_INTERRUPTED、27 PENDING。PENDING没有接受功能评价；表中2/6是固定全槽结果计数，不能写成已执行样本33%功能通过率。phase_snapshot两个重复完成16槽；escape_frame重复1仅完成四共享槽、首分支未知，重复2未启动；masked_ring_alloc全未启动。禁止只筛完整家族重算总体方法通过率。

反馈配对：help0/harm0/no_change4/inconclusive8，四完整配对全部来自phase_snapshot；同臂S/D也仅4对完整同PASS、8对不完整。未观察到完整配对的收益或损害，**无法估计三题族总体IR/反馈收益**。D2照原计划无条件作父样本，没有按D1/D2成绩择优，停止后才隐藏评分。

S已观察的7份RTL（phase首次及最终6份、escape首次1份）IR_spec/RTL_spec/RTL_intent全部PASS、ALL_MATCH；3意图通过，未出现自然规格/意图/实现分歧可供定位。此为有限可观察关联，没有内部思考或理解阶段错误证据。D无显式IR，只报告RTL_spec，不推断理解阶段。人工校准2help/2harm不混入上述真实结果。

## 原始调用与费用账

计划48唯一（24共享、24分支）；四策略各18阶段机会，半共享计划各12。实际20个不同CLI thread各1个完整turn，加1未知预约；不是21个已证实完成的provider回合，也不是48完成。实际半共享预约S-R6、S-F5、D-R5、D-F5合21，包含S-R未知1；已证实完成回合半共享分别5/5/5/5合20。

已知20回合usage小计：input226300、output6156、cache-read126208、cache-write0、reasoning744。reasoning是output子项，不能再相加。第21次provider消耗/usage UNKNOWN，完整批次总usage无法计算，summary保留null；费用无账单，UNKNOWN，不能把未知算0。

|策略|已知半共享input|已知半共享output|已知cache-read|已知reasoning|未报告预约|
|---|---:|---:|---:|---:|---:|
|S-R|56549.5|1603|29696|336|1|
|S-F|56633.5|1603|37120|336|0|
|D-R|56516.5|1475|25984|36|0|
|D-F|56600.5|1475|33408|36|0|

上述已知份额分别求和等于已知20回合总账，未知份额不补0；完整策略含未启动及未知，不能据表比较整体token效率/每PASS成本。actual-analysis.ledger保留完整共享/半共享预约和已知小计；原summary全账null保持。敏感性中的完整成本未知，支持域只观察3个S意图通过、3未启动，不能筛选部分域给总体优势。按机会匹配的S显式IR→RTL与D两早期RTL尝试流程差异、实际token/cache不等及中断缺失仍限制因果解释。

20完整CLI均codex-cli 0.162.0-alpha.17.2，可执行SHA d13914ced6c7af174d8d638db938284231227312104b06a25e9608c632a7daec；请求gpt-5.6-sol/low，后端snapshot未暴露。各回合仅agent_message/reasoning、无工具、1 completed，实际prompt3197..12770字节经stdin完整绑定。已知CLI生成221.628s、已知adapter231.658s；未知请求及中断等待不包含在这些已知执行小计中。不能称完整批次耗时，不能从实际小prompt证明256KiB服务context可用。

## 进程、锁、原证据与核验

interruption/process-check.json记录Win32进程路径关联核查、0匹配runner/CLI，原exec会话55896已不可用；没有终止其他Codex/系统进程。OS advisory lock成功取得，旧run.lock内容字节`0`（hex30）原样保存至interruption/run-lock.original.bin，未删除/截断/重写锁；持久锁文件不等于活跃进程。服务端未知结果和后代树清理仍未独立验证。

run外`../r5_finalize_interrupted.py`把adapter/generate/campaign全部禁用，只调用冻结runner.score；保存437个原文件hash并逐个确认收尾后不变。已有5个公开judge复用，停止后新增24个既定隐藏compile/sim；没有重跑已完成judge或旧模型RTL。包含此前公开判题，共29编译/29仿真、210223事件，nonce/checks/errors/原DUT/向量行逐字节绑定一致。隐藏结果只在确认无运行进程且取得锁后生成。

runs/prepared-v1/evidence-lock.json封存869文件；actual-analysis.json由run外只读分析器产生，核对48槽来源/20精确prompt、原响应/完整事件/usage/唯一thread、33源码、所有新judge原命令nonce与固定资产/模型意图期望、全部2175准备绑定、8066旧绑定及4860 R4seal通过。audit PASS表示原始证据核验通过，**不表示批次完整或方法有效**。旧PREPARATION/packet-lock作为执行前历史快照保持原样，当前状态以本报告和原dispatch/results/summary为准。

同作者三路径参考、固定binary/#2事件、固定参数/短轨迹，非外部独立作者审核/全部状态覆盖/无界正确/最终集/PPA。默认代理34回归3failure/1error/2skip、三个准备失败run、旧公开盲点及旧全PASS负结果保持。本批结束，不自动续批；后续若另有研究需新的明确授权和设计，不能续发未知21或追加27。

审核入口：原run的dispatch/results/summary/evidence-lock及jobs/*/call；actual-analysis（完整行/分层/预算/nonce路径）、actual-gate-audit；interruption的process-check/lock-proof/preserved-before-finalization/closure与原锁字节；本报告和results-packet-lock。停止规则、未知成本及固定分母均保留，供总控独立核验。
