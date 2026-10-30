# Findings — paired feedback study, 2026-10-01

2026-10-09 coordination handoff: FYP project id 59361c93-7a03-48f9-894f-b5dac255f3ed points at parent directory, not the nested Git repository. Execution chat created by explicit user authorization: 01a12095-dd79-7d11-93aa-b1c1f3a4ee0a. Materials are complete for the next step; actual school download/path/hash remains unconfirmed (user reports ~/Downloads file-not-found). Never infer school completion from local package readiness or chat dispatch. Separate execution ledger avoids shared-plan collisions.

2026-10-09 overall audit: existing repository/remote confirmed; gh repo view confirms isPrivate=true. Preserve initial dirty state. Proposal extraction at ../../work/proposal-review/proposal.txt has conflicting model counts (cover/execution >=2 versus section 1.2.1 >=4). Development/conditional-repair results do not satisfy independent final evaluation. Library metadata and 10ns smoke SDC are newer than synthesis guide's missing-library status; real DC/Genus results remain unverified. Current user instructions supersede old shutdown/scale-up permissions: no automatic shutdown; new paid calls require explicit budget. Rechecked VeriRefine and LLM-FSM arXiv abstracts on 2026-10-09: structured representation and stage-specific checking already have direct prior work; contribution remains to be established by controlled evaluation.

Final audit: 178 is retained historical RTL, not additional model generations. Paired raw B summary both_fail=1 actually contains two infrastructure timeouts; read-only audit correctly separates this as one incomplete pair. Same-source VCS/Xcelium evidence exists despite stale VCS historical limitation. Synthesis registry imports=[]; two ready packages each attempts=0. DC/Genus ready packages share RTL 26bdf79291f1dce79294da4019ddf11287a07bc41041b473c9015b646bc1fabd and SDC 71fd56417922a018fb9dd342d2e310e0dec419672d97123df7fbcbb038f9186e. School launch, mapped synthesis completion, mapped functional correctness and timing compliance must be reported independently. Detailed evidence/Proposal milestones/priorities saved in FYP_STATUS_AUDIT_20261009.md.

2026-10-08 integrated workflow: local registry binds each source ZIP hash/backend/case/nonce to one returned attempt; school station menu executes ONE selected case per invocation, auto-collects and ships ZIP then provenance sidecar. Unwritable share preserves outbox for transport-only retries. Local ingestion deduplicates exact ZIP hashes and does not count historical smoke as new commercial validation. Prepared 10 packages/356 tool-case choices from all 178 historical RTL outputs.

Large offline verification: 178 retained outputs re-simulated, 159 PASS/10 FUNCTION_FAIL/9 COMPILE_FAIL, all 178 match originals. Re-ran 163 mutation fixtures, 5 correct references, 25 localization cells. WSL full suite 61 passed; Windows added workflow/transport tests 13 passed. Windows full suite failed two preexisting loopback HTTP mock methods (3 assertions/1 error); urllib reports no proxy bypass for localhost/127.0.0.1. No frozen runtime or system proxy changes. Native ExitWindowsEx privilege probe returned win32_error 0 without requesting shutdown.

- Previous frozen 48-turn study is complete at commit 186357a. Scores 7/8, 7/8, 8/8; all checked IRs were initially correct, so it did not test feedback-driven repair.
- One real erroneous IR exists at evidence/fsm48/jobs/m02__rt_sequence__table__s001/stage1/response.txt. It sends S4 on input 0 to S3 instead of S2. Preserve its exact bytes and provenance.
- Existing FSM interpreter handles data-only single-bit Moore FSMs, explicit reset, finite graph equivalence and timed pre/post-edge simulation.
- Existing guarded Codex CLI adapter uses ChatGPT login, disables tools and records usage. Existing batch subprocess cleanup and Yosys replay can be reused.
- Current account usage readout: 63% used in the available window; no credit purchase or reset is needed/authorized. This is account-wide, not experiment-specific.
- Repository is clean. Existing source/benchmark locks must remain unchanged. New development families and held-out tasks will live in a separate bank.
- User explicitly authorized autonomous completion, progressive scale-up, GitHub sync inherited from prior turns, and shutdown after verified completion; no intermediate confirmation is needed.
- Frozen bank contains four genuinely different new development behaviors and two held-out candidates. Candidate hold-out status is limited: offline verified and not model-used, but no external expert review or exhaustive similarity audit is claimed.
- Paired prompts differ only in computed public feedback. No fresh first-stage generation is charged in this conditional repair experiment; prior natural-IR provenance remains recorded.
- First natural-error paired result: terra feedback PASS vs control FUNCTION_FAIL, with control still classified SPEC_TO_IR_ERROR. Unlike the previous 48-turn study, both conditions began with identical erroneous IR bytes. Wait for all fixed samples; do not select or expand based on this early result.
- AoT v1 full framework/setup checked: 156 tasks, n=5, temperature 0.6, output cap default; Table 2 generated tokens is not total input/output cost. Multi-stage path does not imply exactly three calls. Added revision-specific notes and fixed-IR estimand distinction to FSM_LITERATURE.md.
- Reporting caution after sleep: raw runner pair_counts classifies the two TIMEOUT rows as both_fail. Final post-hoc audit must separate infrastructure-incomplete pairs from functional both_fail, preserving raw evidence and planned denominators.
- Stage B observed terra/request_delay/state_output repeat 1 control FUNCTION_FAIL/BOTH_DIVERGE. RTL omits wait state and raises q on the accepting edge; specification requires q=0 then q=1 on next edge. Candidate IR instead has q high for both wait and response, so RTL differs from both IR and spec. Paired feedback RTL retains WAIT and passes. Fixed judge reports 3247 spec mismatches and 1732 IR/RTL mismatches; no unique internal reasoning cause is inferred.
- Final result: 42 both-pass complete pairs, 5 feedback-only complete pairs (2 natural overlap / 3 injected request-delay), 0 control-only, and 1 infrastructure-incomplete pair. 94 retained outputs synthesize; 89 pass functionality. CI 36774716313 passed all 43 tests and read-only evidence audit.

- New hypothesis: public example feedback may miss valid-schema single-edit semantic faults beyond the 12 selected cases. Previous model study cannot calibrate correct-IR/wrong-RTL localization because all initial IRs were erroneous. Both gaps can be examined with finite offline mutation fixtures, without new model calls.
- Exhaustive declared single-edit enumeration produced 163 non-equivalent mutants: rt_sequence 51, sticky_alarm 19, event_parity 9, request_delay 33, debounce3 51. Original public examples miss 30 (19/2/0/1/8 by task). Greedy development counterexample additions number 12 (8/1/0/1/2); augmented contract detects all 163 at IR level. Real Icarus confirmation pending.
- Concrete public blind spots: sticky_alarm edge_05->S0, input 111 loses latched alarm (expected1/observed0); request_delay edge_04->S0, input10010 responds too early; debounce3 edge_02->S1, input1011 improperly accumulates nonconsecutive ones; rt_sequence edge_00->S1, input0001 false positive. These are checker coverage limits, not claims about natural LLM error rates.
- Real simulator confirmation: no fixed hidden-test misses among the 163 faults. Public coverage rises from 133/163 to 163/163 with a separate 12-example augmentation; this is development-fitted coverage, not LLM efficacy. New public check CLI has a tested absence of private-oracle dependencies; 25 actual Icarus calibration cells cover all five diagnostic classes.
- Verified end state: original public-check blind spots reproduced by CLI; 12 separate development examples cover all 163 enumerated faults; original hidden tests catch all 163; 25 localization fixtures pass. WSL 48/48 and GitHub CI 36785360906 pass. Next research question is generalization to composite faults and separating added-example information from executable-feedback benefit.
# ECE desktop handoff, 2026-10-08

- User confirmed Omnissa Horizon Client and server vdi.ece.ust.hk; school VPN is now enabled. Screenshot showed connecting, not a completed Linux desktop session.
- New capped paired replay reserved 4/16 slots (two models, control/feedback real_overlap); all failed with HTTP 403 at Codex model service. Two requests followed the VPN change. No effective generation, no efficacy estimate; 12 tasks remain pending. No failed call retries.
- Separate transport modules preserve frozen experiment source hashes. VCS/Xcelium packages use retained paired-a32 m01 real_overlap control, not fresh generated data.
- ECE only supports manual host simulation in this context; no SSH, supported EDA batch or scheduler. Folder sharing and actual commercial tool availability remain unverified.

2026-10-09 API workbench: seven new Windows tests passed, including synthetic loopback HTTP -> actual Icarus -> report and resume with exactly one request. No paid model calls. CSV local configuration is Git-ignored. PDF review requested during regression; six pages extracted with pypdf; fitz unavailable, initial console GBK failed, fixed UTF-8 output. ELEC5550 requires DC, PrimeTime, Innovus, Tcl and Nangate45; Horizon/DUO school login. Existing CLI/FSM runtime untouched.
## 2026-10-09 unified FYP workflow

- Original FYP tools are connected through lab.ps1: configured API generation, fixed Icarus tests, independent Yosys review, frozen VCS/Xcelium packages, return validation and reports. ELEC5550/DC/Innovus remains deferred by the user.
- Verbatim mode preserves the UTF-8 file bytes, including CRLF, Unicode and leading/trailing whitespace. The actual API messages array contains exactly one user message. Loopback request inspection verifies this; arbitrary prompts without a matching fixed testbench receive GENERATED_UNVERIFIED, not a functional score.
- Shared-folder and Git routes retain one manually selected commercial case per invocation. Git results use independent result branches and a temporary index, preserving HEAD and staged changes. Failed upload retries only transport; result ingestion verifies hashes and never checks out returned code.
- Ten unchanged historical packages contain 356 case/tool selections (178 retained RTL outputs, each offered for VCS and Xcelium). Availability in the menu does not mean those commercial simulations passed. The new Git route still needs first real school network/authentication validation.
- Windows eight new tests and Linux 28 related tests passed with synthetic API/commercial fixtures and real local Icarus/Yosys. No paid model calls or new school EDA runs were made during script development.
2026-10-09 school synthesis integration: DC X-2025.06-SP2 and Genus21.14 startup are evidenced by user record; no cell-library paths yet. Separate synthesis template completes RTL-to-mapped-netlist flow only after explicit libraries/corner/reviewed SDC. COMPLETE plus receipt/artifacts becomes COMPLETED_REVIEW_REQUIRED, never automatic synthesis/functional/timing PASS. Corner label is metadata; chosen libraries and report units require review. No library bytes exported. Dedicated ECE-Synthesis sharing and payload/result hash binding keep old Yosys/VCS/Xcelium results intact.


User verified Nangate NLDM typical .lib/.db readable via find exit 0. Liberty reports process1.00,1.10V,25C,time1ns,cap1fF. DB contents/actual tool load not verified. Source-reviewed sequence_detector has posedge clk and negedge rst_n; 10ns smoke-only SDC, reset false path explicitly excludes recovery/removal.

2026-10-11 403 cause isolated: original adapter clean_env omits network proxy, although Windows has a working configured proxy. Same unauth endpoint direct403 HTML/proxy401 JSON, then same-model authenticated smoke succeeds through new adapter. No model substitution or CLI upgrade required. Account ordinary usage allowed at71% weekly consumption. Equal-call R2 cannot claim exact token equality because current CLI adapter sends no output-token cap; preserve all observed usage and cost differences.

2026-10-11 09:19 R2 complete/accepted: independent1073-file/63-source-lock/20CLI-completion/60Icarus-receipt audit matches regeneration10/10 versus feedback9/10;0help,1harm(request_delay early q),9no_change. No API errors/retries; finalization-only Windows lock fix preserved frozen sources/results. No efficacy improvement established, no general harm conclusion from5development families. Current experiment ends; no new batch dispatched. Next research candidates: new independently referenced temporal families with same strong regeneration control, or verified-IR deterministic-vs-LLM translation to isolate implementation error. Details/notification/cursor:17 in FYP_EXPLORATION_REVIEW.md.

2026-10-11 10:20 R3 completed/independently accepted:975files/30source locks,24CLI responses,32nonce-bound simulations,528464event bindings; first8/8 and both arms8/8 fixed-hidden PASS,0help/0harm/8no_change, no natural repair cases. Plan-role restoration after judge.stage collision verified field-by-field, no reruns. Equivalent-implementation scope correction done. One report-only EXTRACTION_ERROR classification caveat sent; no new experiments. Focus next on finite semantic coverage/reference audit or properly isolated structured-intent versus feedback experiment, not blind scale-up.

## 2026-10-11 v2工程边界

真实字段与格式边界夹具支持修复role被stage覆盖和EXTRACTION_ERROR分支终止问题。人工2help/2harm只校验分类，不是模型收益。离线prompt完整保留不证明CLI能够传输超长prompt；默认代理回归失败与隔离loopback通过须分开报告。R3全首次PASS的研究限制不因工程修复改变。

## 2026-10-11 v3总控验收

v3工程结果说明Windows argv会阻止12个超长测试prompt运输，stdin可保持完整UTF8数据进入本地兼容接收进程。该证据不证明真实模型上下文接受或研究收益；无后代夹具时kill_tree调用仅结合回执支持直接进程终止，不能称整棵树清理实测。

## 2026-10-11 13:23 R4原始结果独立验收

R4有真实模型中间意图，但12意图与全部36RTL三路均通过，仍是天花板；JSON和线性均受控IR，不能外推有/无结构化表示对照。实际token与cache不同，无严格等token收益；人工校准定位不等于自然错误定位。建议先核查独立判据鉴别力并设计真正no-IR消融，不继续同批扩容。

## 2026-10-15 transaction-alignment-v1完成独立验收
固定单批11IR/11compile/11sim、0模型、11执行+1预声明未执行完成。总控独立24源/20354历史/270run文件，1760native采样、1760IR闭式手算、320同映射相位及时间FIFO/复位/offer账全部核对一致。11实跑意图6PASS/2人工失败/3不可评估；合法延迟与结构差异通过，提前消费和跨复位残留检出，两specPASS而接受取消集合不同正确不可评估。具备另行准备外部来源契约盘点基础，尚无自然错误定位或IR/反馈收益结论，不自动启动新来源/模型，原负结果与局限保留，定时任务仍暂停。详见REVIEW与validation/fyp-exploration-review/transaction-alignment-v1-completion-coordinator-audit.json。

## 2026-10-16 FYP/T Support Scheme同步（预算对话转述，待官方细项核验）
来源：预算对话01a13402-8336-70e0-8c54-fa1108efbf38转述用户贴出的系内邮件，未独立核验申请表细项。邮件载：有demo/外部比赛潜力且预算超原有额度，项目上限HKD20,000（非已获批）；截止2026-10-21，First apply, first approve，预计11月下旬通知；申请https://ust.az1.qualtrics.com/jfe/form/SV_5pVJHYb21hOMAm2；需≤3分钟视频、3–5页PPT、Word详细交付清单、导师邮件同意，获资助后支出预算报告。视频/PPT覆盖简介、资金理由、全部交付物及必要性；邮件未要求真人出镜或完成系统。获资助后需至少MakerSpace留存demo或代表系外部学生比赛承诺之一。
建议MakerSpace软件演示+离线回放尚未确认，纯软件资格/展示电脑/留存维护期限待核，不自行采购硬件或承诺比赛。交付拟为演示原型、核验案例波形、受控比较与错误分析、复现实验包、部署说明及final report/poster/presentation，对齐2027年4–5月。不能宣传已证明IR/反馈收益，开发人工校准与独立最终集分开。
proposal暂定HKD1200订阅+500 API/可选embeddings=1700，不是已知拨款/实支。基础额度、模型价格、申请金额/报销资格未定。历史720调用场景=240初始+240额外条件+240最多两轮修复，未含配对重新生成/开发/重试/demo，非执行协议授权；至少2模型与部分正文至少4模型冲突待统一。现金与资源账分开，调用/token/cache/reasoning不重复计费、反馈/技术重试、本机时间/编译仿真/超时、学校手动运行排队人工时间分别记录；等调用不等token、等费用不等算力、学校零现金不等零资源。四页英文PPT文案+约330词稿仅草稿无文件，金额[X]。
本同步只记项目约束，不授权付费模型、采购充值、扩批、学校操作、发信或提交；不因截止改变研究边界，10月底里程碑不能依赖预计11月底才公布的资金。

## 2026-10-16 课题方向重新核查（研究中，不改当前实验）
用户提供原始XZY01题目明确主线自然语言直接生成RTL，并探索prompt engineering/RAG，QA可选、benchmarks支持。proposal.txt第195–202及397–419行明确检索语言规则/通用设计知识/版本化工具文档；排除近重复答案；无检索和固定上下文控制；反馈须等调用重新生成对照。当前固定输入直接RTL三模型基线仍保持原规则，不将研究候选自动合入。
初查一手文献：RTLCoder TCAD2025主打数据构建与专用模型训练，不是RAG效果证明；RTLFixer DAC2024结合compiler反馈/RAG/ReAct，主要是语法修复，不能当作一次生成语义正确性收益；ChipNeMo研究工程QA/EDA脚本/bug分析，不能直接当RTL功能通过率依据；RTLRepoCoder是仓库代码补全且结合微调，任务不同。VeriRAG KG+vector生成方向需进一步核小规模/参考/对照边界。跨模型同一条件prompt必须一致；跨RAG条件完整prompt必不同，是未来预声明实验变量，未经新冻结不执行。

方向核查补充：发现更贴近本课题的一手工作DeepV（arXiv:2510.05327v1，https://arxiv.org/html/2510.05327v1），直接在RTL生成时检索Verilog示例、无需RTL专用训练，包含相关性过滤/动态示例选择；因此“首次把RAG用于RTL”不能作为创新主张。可探索的有限差异是假设驱动的时序/复位兼容过滤，与普通相似度检索、固定通用上下文、无检索比较，固定原题及测试，规则与语料在开发集冻结，排除测试答案/近重复及私有向量；功能收益和检索错误导致回退分别报告。DeepV正文已读方法，未完整复现或审核其语料独立性；不引用宣传百分比为本项目收益。VeriRAG作者PDF访问Internal Error，IEEE摘要可访问，暂不依据其高通过率作推荐。
候选优先级：生成前的语言规则/时序知识RAG；简单固定检查清单作为对照；若基线真实语法失败明显才考虑RTLFixer式诊断检索修复，须另立调用预算与重新生成对照；QA为可选演示支线，ChipNeMo主要证据在QA/脚本/bug分析。当前用户转问RAG通俗定义，先解释概念；没有改任务数据/冻结提示词/模型执行权限，没有部署RAG或发起新批。后续研究方案需与当前三模型同prompt基线分开。

2026-10-24 项目目标核查及有限离线分析完成：validation/objectives-review-20261024-v1/REPORT.md、analysis.json、evidence-lock.json。按用户“不调用模型/不改原题和RAG”限定自行开展为既有240回执分析与20条冻结检索独立复现；0模型/网络/EDA，无生产修改。240状态和120配对交叉一致，585证据hash保持，6/287/30锁通过，80请求组除model一致；18段实际取回9段，LR018在19题、LR015在18题，输入token均值约增至2.22倍；不据此推断因果。已确认2题全过、其他7题不升级资格。优先补参考/时序契约，再准备冻结原方法新题两臂复验（拟144槽）；此前三臂216槽仅备选且需明确允许提示变更，不叠加不启动。QA后置、学校综合不自动启动。新分析器首次source-lock相对路径解析失败已修正，仅离线分析重算，不涉及模型重试。预算计划未改，使用rtl-batch总控legacy计划。
