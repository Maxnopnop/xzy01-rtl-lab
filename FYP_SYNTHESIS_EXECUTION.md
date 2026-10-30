# FYP 学校单案例综合执行记录

日期：2026-10-09（Asia/Shanghai）。本记录供总控读取；不自动向其他对话发送消息。

## 接续核查

已读 AGENTS.md、README.md、ARCHITECTURE.md、task_plan.md、progress.md、findings.md、ECE_SYNTHESIS_GITHUB.md、FYP_SYNTHESIS_HANDOFF.md。

实际仓库：`E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch`；HEAD：`aa6ff553fd6b60bbd3cc5b1962934c4bd82f7546`。

接续时已有修改：ECE_SYNTHESIS_GUIDE.md、README.md、findings.md、progress.md、task_plan.md。已有未跟踪文件：FYP_STATUS_AUDIT_20261009.md、FYP_SYNTHESIS_HANDOFF.md、elec_common.py、elec_menu.sh、elec_school.py。全部保留，不重写总计划文件。

## 固定范围与来源

- 样本：paired-a32 / m01__real_overlap__s001__control；顶层 sequence_detector。
- 顺序：学校下载确认 → 实际路径哈希校验 → 新目录解压 → DC 单例手动运行 → 回收与审阅 → Genus 另一次单例手动运行 → 回收与审阅。
- 备用 ZIP：ece_git_packages/xzy01-synth-local-20261009.zip；交接记录大小 26785 字节；SHA256 `13b9b9213082c0e81b0388620fbb92b793a274ceb4319be9f9e84de5113f453a`。
- RTL SHA256：`26bdf79291f1dce79294da4019ddf11287a07bc41041b473c9015b646bc1fabd`。
- SDC SHA256：`71fd56417922a018fb9dd342d2e310e0dec419672d97123df7fbcbb038f9186e`。
- 原结果 SHA256：`e64a1cf2e5a93b564cca2a33890f81dd0ac56f79f11e3b0745925465ab48d723`。

以上哈希来自已读交接记录；本次未重新校验学校文件。

## 当前执行状态

首步待用户反馈：在学校 Linux 浏览器下载原始 ZIP，确认下载完成及实际保存路径；已有下载可从浏览器下载列表定位。此前共享读取超时且预设 ~/Downloads 下找不到文件，不能继续假定路径校验或启动 EDA。

DC：尚无本次真实执行回传；工具执行、映射网表、报告审阅、网表功能与时序结论均待证据。

Genus：待 DC 回收审阅完成后单独推进；尚无本次真实执行回传。

## 验收边界

分别核对版本/命令/退出码/日志、读取展开链接映射、未解析引用/锁存器、网表与报告、nonce/输入锁/学校库指纹/PVT/单位，以及面积、时序、约束覆盖、违例、豁免和警告。退出 0 或文件齐全不能自动判功能正确或时序达标。

已有 Icarus/VCS/Xcelium 同例各 1840 检查、0 错误仅证明原 RTL 固定测试通过。综合网表功能需独立网表仿真或等价证据；若缺失明确记录未验证。10ns 仅流程测试，异步复位释放与 recovery/removal 未覆盖。

不新增 RTL/付费模型调用，不关机，不 SSH 或批量 EDA，不上传库、密钥或许可证。仅校验后的白名单结果可回传；完整商业日志保留本机，不未经审查全量提交。

## 后续学校反馈：定位与校验通过

用户在学校终端 `smaap@ecelvd702` 用 find 定位到 `/staff/ee/smaap/tsclient/FYP/xzy01-synth-local-20261009.zip`。该位置属于 Horizon 共享路径；此前超时不能代表当前仍不可读。

用户随后执行 `timeout 30s sha256sum`，返回 `13b9b9213082c0e81b0388620fbb92b793a274ceb4319be9f9e84de5113f453a`，与冻结备用包一致。依据为用户粘贴的学校终端输出，尚非机器导入回执。

学校文件路径和哈希门已通过，取代上文初始待确认状态。下一步：解压到学校家目录下新的独立本地目录并查看顶层文件；尚未启动 DC 或 Genus。

用户确认解压成功：`/staff/ee/smaap/xzy01-synth-utdgs9qw`。顶层包含 README.txt、ece_synth_common.py、ece_synth_school.py、start_local_dc.sh、start_local_genus.sh、两个冻结内层 ZIP 和 synthesis-catalog.json，与备用包预期一致。本机只读核对原 ZIP 内 start_local_dc.sh：脚本自行切换到所在目录，固定选择 DC 包 d47c8919，结果留在本地 returned/。下一用户步骤为单独 bash 启动 DC 入口，等待输出；启动成功及综合结果尚未确认。

2026-10-15 用户执行 DC 启动入口后返回终端：学校 attempt 为 `/staff/ee/smaap/xzy01-synthesis/session-20261015T025958Z-32ce78fe`，显示 `Return copied; no synthesis started by ship.`，未显示 Missing 或 ERROR。核对本机 runner：session 顺序为 run → collect → ship；ship 的该提示只说明传输不重复综合，不能据此判定 DC 未运行或综合成功。下一步只读 execution.json 与 doctor.json，确认实际执行状态、退出码及库预检查；不重复启动 DC，Genus 仍未授权进入本轮步骤。

用户随后提供 execution.json / doctor.json：package_id 为 `synth-dc-20261009T100543Z-d47c8919`，nonce `737a9322e3db40bfb390140ed5c6487e`；执行 20261015T025958Z 至 20261015T030016Z（北京时间 10:59:58 至 11:00:16），status=EXITED、returncode=0。主机 `ecelvd702.ece.local`，预期版本 X-2025.06-SP2（实际版本待日志）。doctor missing=[]；typical .db 可读、1851392 字节、SHA256 `3c205f46310315953d992fb014e814a1f12e9cb2a0030f900dc366131f7fc425`；setup SHA256 `d61f2679adffd87d71e75ae05d65c5f37b64d4694d283fd1ecbb6ed2a85b1cdf`；SDC 哈希与冻结值相同。doctor 仅预检查库文件可读性/指纹，不证明工具真实加载或许可证可用。证据仍为用户粘贴，尚待导入原始回传包。当前仅确认启动流程正常退出；完成凭据、实际版本、网表/报告、映射/功能/时序尚待核对。

用户提供下一段终端输出：receipt 为 `XZY01_SYNTH_V1 737a9322e3db40bfb390140ed5c6487e COMPLETE`；tool_version.log 显示 dc_shell X-2025.06-SP2 / build Aug 27, 2025，另有 ASLR/VCS_SAVE_RESTORE_INFO 提示，待结合原始日志判断影响。文件清单：outputs/constraints.sdc 1137、netlist.v 1391、design.ddc 24576；reports/constraints.rpt 675、timing.rpt 6535、area.rpt 1154、check_design.rpt 2 字节。不能将 2 字节 check_design 报告视作结构检查通过。outbox 生成 `return-synth-20261015T030016Z-5cafd3c5.zip`（30939 字节）及同名 .json（318 字节）。下一步仅回传这两个由冻结 runner 白名单收集的文件至已确认的 FYP 共享目录；完整商业日志按本机私有证据保存，不提交 Git。来源绑定/原始包导入/报告审阅/网表功能/时序结论仍待核验，Genus 尚未启动。

## DC 原始回传与报告审阅（2026-10-15）

用户将 ZIP 和 JSON 复制到学校 tsclient/FYP，本机在 `C:/Users/A/Documents/FYP` 读取到原文件。ZIP SHA256 为 `db83a99cf47f9e103ddf82af23ced1f875c1d769cdc611e76fce1a243352a875`，与 sidecar 一致；CRC、21 个成员无重名、白名单检查通过，无标准单元库文件。通过现有 ece_synthesis.ingest 导入：1 imported、0 invalid，注册状态 `COMPLETED_REVIEW_REQUIRED`，保持该状态，不改为自动 PASS。原始解压证据位于 `workflow/synthesis/returned/db83a99cf47f9e103ddf82af23ced1f875c1d769cdc611e76fce1a243352a875/`，该路径与 registry 均被 Git 忽略；完整商业日志只本机保存。

输入锁 SHA256 `334fe46d6e9e252eecc2a5bf3a58179d5d46894c778734dcfc45f390c3ea3c98`、包 ID/nonce、RTL/SDC/脚本与原包一致。tool.log 确认 DC X-2025.06-SP2 实际读取 Nangate typical .db，RTL 编译、展开、链接和映射完成；链接明确报告没有消息，报告中没有宏/黑盒。启动 ASLR 提示后流程正常完成，未见该提示阻止本次综合，未主动修改系统设置。

审阅结果：

- 网表：12 个标准单元（9 组合、3 时序）；3 个 DFFR_X1，未见锁存器实例。面积报告黑盒数 0；总单元面积 25.270001（报告库面积单位，未另行验证其物理单位）；总面积/互连面积 undefined，不能解释为布局后面积。
- check_design.rpt 实际内容为 `1` 加换行；冻结 Tcl 在 compile 前另有 `if {![check_design]} {error ...}`，执行走到 COMPLETE，支持该次综合前结构检查成功。没有 compile 后独立 check_design/check_timing 的完整报告，不将两字节报告扩大解释为后综合网表完整检查。
- outputs/constraints.sdc 明确 `set_units -time ns ... -capacitance fF`，确认本次 DC 时间与电容单位；报告工作条件 typical，电压/温度沿用库元数据，未取得工具完整 PVT 属性转储。
- timing.rpt 是 max/setup 报告，列出 4 条路径（-max_paths 10 是上限）；最差已报告 slack +8.65 ns（state_reg[2] → sequence_detected），其他 +8.77 ns。
- **constraints.rpt 明确有 3 条 min_delay/hold 违例**：state_reg[1]/D -0.07 ns、state_reg[0]/D -0.03 ns、state_reg[2]/D -0.02 ns。因此当前约束下时序未全部满足，不能称 timing PASS。未收回完整 min 路径细节，暂不推断每条 hold 的起点或修复方式。
- 输入约束：10 ns 理想时钟，0.1 ns uncertainty/transition；data_in max/min 1/0 ns；输出 max/min 1/0 ns，负载 5 fF；rst_n false path。无独立全覆盖/未约束路径报告；异步复位释放、recovery/removal、安全释放、布局布线/实际时钟树/多角签核均未覆盖。
- 功能：本次未运行综合网表仿真或形式等价；原 RTL 的仿真记录不替代该证据，综合网表功能仍未验证。

DC 回收及首轮报告审阅已完成，保留 hold 失败和证据缺口，不修改原 RTL、冻结 SDC 或重跑掩盖结果。下一阶段可以单独启动既定 Genus 同源单案例，作为独立工具证据，不将其用于覆盖 DC hold 违例。

补充复核通过：原始 run/plan.json 与 result.json 哈希匹配包记录，全部 21 个回传文件哈希与导入索引一致，网表单元数和 hold/slack 数值由只读脚本复核。机器可读审阅摘要：`workflow/synthesis/reviews/dc-20261015.json`；原 ZIP/JSON 留存：`workflow/synthesis/raw/dc-20261015/`。以上路径均确认 Git 忽略；本轮未提交/推送任何商业日志，未改动总控计划文件。planning-with-files 解析器未选出命名计划，遵循总控分工继续使用本独立 ledger；task-quality-check 用于上述证据验收。

## Genus 学校执行（2026-10-15）

DC 回收审阅后用户单独执行 `bash /staff/ee/smaap/xzy01-synth-utdgs9qw/start_local_genus.sh`，创建 `/staff/ee/smaap/xzy01-synthesis/session-20261015T031157Z-48f6af9a`，随后显示 Return copied 并返回终端，未重复启动。

用户粘贴 execution.json / doctor.json：package_id `synth-genus-20261009T100543Z-07992262`，nonce `87bbadf80e2c40ae89ca8f59602ed2a7`；20261015T031157Z 至 20261015T031230Z（北京时间 11:11:57 至 11:12:30），status=EXITED、returncode=0。主机 `ecelvd702.ece.local`，预期版本 21.14-s082_1（实际版本待日志）。setup SHA256 `808cd3d8c33b38127ce4ea04007a8520e802a013dc289e0e72388bbf6918cc18`；typical .lib 可读、6691483 字节、SHA256 `2efd0b32eb580e4e60e72fc0575bb3bc69aac907c91d908442e4ae6d7fe55895`；SDC 哈希与 DC/冻结输入相同；missing=[]。doctor 不证明工具真实库加载或许可证状态。下一步只读完成凭据、实际版本和 outputs/reports/outbox 文件清单，再回收原 ZIP/JSON 并审阅；当前仍不能判综合、网表功能或时序通过。

## Genus 原始回传与报告审阅（2026-10-15）

用户确认 receipt `XZY01_SYNTH_V1 87bbadf80e2c40ae89ca8f59602ed2a7 COMPLETE`、实际版本 21.14-s082_1；生成 netlist.v 1433 字节、constraints.sdc 1166 字节、area.rpt 800 字节、timing.rpt 2134 字节、check_design.rpt 265 字节。outbox 回传 `return-synth-20261015T031230Z-3f77c8ce.zip` 22681 字节及同名 JSON 321 字节。用户复制到共享目录，本机读取原始文件并校验 CRC、ZIP SHA256 与 sidecar、19 成员无重名和白名单，通过现有导入器：1 imported、0 invalid，状态 `COMPLETED_REVIEW_REQUIRED`。

ZIP SHA256 `2ea7f2d2467d8b02d3ee1e6c889eb94e4d37df093a036450e6e4a41ea65186d3`；原始解压证据在 `workflow/synthesis/returned/2ea7f2d2467d8b02d3ee1e6c889eb94e4d37df093a036450e6e4a41ea65186d3/`。RTL、结果、计划、输入 SDC、包脚本及 nonce 通过现有输入锁与来源绑定检查，使用的 .lib 与 DC .db 是分别指纹绑定的库文件，不宣称两种库字节或工具内部模型相同。

审阅结果：

- tool.log 确认 Genus 21.14-s082_1，Periodic Lic check successful，完成 HDL 展开、syn_generic、syn_map、syn_opt、SDC 导出并 Normal exit。版本日志的 `This build will expire on 4/11/2023` 保留为历史构建提示；本次 2026-10-15 实跑未被其阻止，不推断未来可用性或许可有效期限。
- 工具实际读取典型库，LBR-412 记录 PVT (1.000000, 1.100000, 25.000000)。check_design -unresolved 在映射前报告无未解析引用、无空模块；没有映射后独立完整结构/时序覆盖检查。
- 映射网表 12 单元，其中 3 个 DFFR_X1，未见锁存器实例。面积报告单元面积 25.536，报告 Net Area 0、Total Area 25.536 属库/wireload 估计，不是布局后面积。实际 wireload 为 enclosed、5K_hvratio_1_1，DC 为 top；面积/时延差异不是方法效果比较。
- timing.rpt 只有 1 条 late/setup 输出路径，slack +8660 ps = +8.660 ns；起点 state_reg[1]/CK、终点 sequence_detected，数据路径 240 ps，required 8900 ps。输出 SDC 时间单位 1000 ps (=1 ns)、电容 1 fF，10 ns 理想时钟与同源输入约束保持。
- **本次 Genus 冻结脚本未生成 hold/min 或 all-violators 报告**，因此 hold 状态未知，不可由一条正 setup slack 推断全路径时序满足；不替代 DC 已知 3 条 hold 违例。
- 警告：LBR-9 共14次，ANTENNA_X1/FILLCELL_X* 无逻辑输出、被标不可用，返回网表未使用这些单元；LBR-81 共11次，非单调 wireload 表被工具自动抬点调整，包含本次实际使用模型，时延结果应受此限制；CPI-506 一次，无 power intent 导致 commit_power_intent 不能执行，本阶段未提供低功耗意图，不作低功耗/PPA功耗结论。不得为消除警告修改冻结库或原模型 RTL。
- 网表中的 `Verification Directory fv/sequence_detector` 注释及日志写出 formal verification information 仅说明辅助文件生成，未执行独立等价检查。综合网表功能仍未验证。
- 10 ns 仅 smoke 假设；复位 false path 排除了 recovery/removal，未验证复位释放安全；未有 check_timing/未约束路径报告、布局布线/时钟树、多角签核。

本阶段 DC→回收审阅→Genus→回收审阅顺序已完成；两次真实学校映射与证据回收已确认，功能验证及完整时序仍有上述缺口。保留所有失败/警告和原始商业日志，不自动补跑或修改冻结设计。

Genus 补充库解析信息：LBR-40 为 Info、3 次不支持的 Liberty 构造，回传日志未说明具体构造；LBR-155 为 Info、1 次 timing_sense 与功能的 unateness 不一致（工具保留 timing_sense）；LBR-162 为 Info、15 次同时存在正/负 unate arc 而处理为 non_unate。这些均为本次库解释限制，尚不能定位到所用单元或保证对时序无影响。工具日志共 26 条 Warning 消息，无以 Error/Fatal 开头的实际消息；并不替代功能/时序验证。read_sdc 统计各执行命令 failed=0。

Genus 补充复核通过：原 plan/result 哈希、全部 19 个回传文件哈希、12 单元/3 DFFR_X1 和跨工具 RTL/输入 SDC 一致性；实际网表未使用上述 ANTENNA/FILLCELL。原 ZIP/JSON 留存在 `workflow/synthesis/raw/genus-20261015/`，机器摘要 `workflow/synthesis/reviews/genus-20261015.json`；综合索引 `workflow/synthesis/reviews/school-single-case-20261015.json`，两工具均保持注册状态 COMPLETED_REVIEW_REQUIRED，人工审阅结论与导入状态分开保存。

### 阶段交付状态

| 项目 | DC | Genus |
|---|---|---|
| 真实学校执行/回收/首轮审阅 | 已完成 | 已完成 |
| 映射网表与来源绑定 | 已确认 | 已确认 |
| 已报告 setup slack | 最差 +8.65 ns（4 条 max 路径） | +8.660 ns（1 条 late 路径） |
| hold | 3 条违例，最差 -0.07 ns | 未报告，未知 |
| 综合网表功能 | 未验证 | 未验证 |
| 复位释放/完整约束覆盖/签核 | 未覆盖或证据不全 | 未覆盖或证据不全 |

下一阶段建议：在保留原 RTL/模型结果/本次网表与约束的前提下，另立版本化验证任务完成综合网表仿真或独立等价、补齐 Genus hold 与两工具约束覆盖诊断，再讨论 hold 修复与正式约束。当前阶段不自动扩大到新 EDA 运行。本记录供总控直接读取，未向其他对话发送消息。

## 用户授权继续：综合网表固定功能测试

用户要求继续完成明确的功能验证，并尽量只需一次粘贴学校命令。新阶段准备独立 `ece_gate_check.py`，复用原 Xcelium 已验收测试台与 rt_sequence.hex 的原字节（1840 检查），分别验证 DC/Genus 本次网表。不修改冻结 RTL、SDC 或旧综合包；每次入口仍只选一份网表，无 EDA 循环/SSH/新增模型调用。先 DC 回收审阅，再 Genus。

成功条件：实际 Xcelium 正常退出、唯一新 nonce 回执、恰好1840 checks、errors=0，并绑定本网表/原 RTL/测试台/向量/学校单元模型指纹。不作全输入形式等价或物理时序结论；不加载 SDF，使用 -nospecify 禁用单元 specify timing。固定测试台仍保留原 #2 采样延时，不能对整个仿真施加全局零延时（否则会改变测试台激励时序）。参考 Cadence 官方 Gate-Level Simulation Methodology：https://www.cadence.com/content/dam/cadence-www/global/en_US/documents/training/gate-level-simulation-wp.pdf 。

脚本将在已知学校 PDK 根下受限查找单一 Verilog 模型，要求覆盖本网表所有单元；找不到则停止，不临时编造替代门模型。只回传白名单，绝不打包学校库或许可证。每次新建独立工作目录，180秒超时、不自动重试；完整原始日志本机保存。

本机准备过程纠正：一次过宽 rg 文件清单被截断，后续使用已知精确案例路径；旧回传目录没有 run.tcl，改用已验证 school_bridge 中的 run/exit 模板，不依赖该缺失文件。以上均未执行学校 EDA。

一键功能包 v1 已准备并放到 `C:/Users/A/Documents/FYP`，学校对应已确认共享目录 `/staff/ee/smaap/tsclient/FYP`。用户只需一次粘贴 `bash /staff/ee/smaap/tsclient/FYP/start_gate_dc.sh`，该入口固定 DC 一份网表，自动校验 ZIP 哈希/CRC/成员及输入锁，解压到学校新本地目录，定位学校单元模型、运行 Xcelium、判1840次回执并只回传白名单 ZIP/JSON。Genus 的独立入口已准备，但须等待 DC 反馈/回收审阅后再给操作，不合并循环运行。

包：`workflow/gate-check/xzy01-gate-check-v1.zip`，6150字节，SHA256 `0ff09de702ea2f428c8c858ccd33eacfcd173cfd2edaeaa4688261d9894964a7`；版本元数据 `workflow/gate-check/release-v1.json`。DC 网表哈希 `d9f110ee9c4ac7df3e546b24062a4ef2e5452363e9c65386ae1f2e74a192b9d1`；Genus 网表哈希 `24a9fe2f270033a5bf29a2f7f2f4e7e9a39337c63ce6788a182f574a2bc1fd2b`。TB SHA256 `6abb900b5f8cae1ea0ab98321c1830bd58f4132c75efb676b9cc4250a5e90e4b`；向量 SHA256 `6f656556d2940534fe990384d84ed61cb498a683531b24ee599374d98aec4c40`，均复核与历史固定测试原字节一致。

本机验证：3 项 unittest 通过（正确/错误 nonce、重复凭据、非零退出、不完整检查、真实错误拒收；单元模型必须覆盖全部单元；回传排除库/许可证/二进制）。Python 3.6 AST 兼容、bootstrap/runner 语法、包内所有锁、CRC、两份共享启动脚本哈希核对通过。测试均是本机离线脚本验证，不是学校综合网表功能成绩；学校实际 PDK Verilog 模型路径与新仿真结果仍待首次执行反馈。没有修改旧综合包、历史成绩或总控计划文件。

首次学校 gate 入口失败：`bash /staff/ee/smaap/tsclient/FYP/start_gate_dc.sh` 报 No such file or directory；新功能仿真尚未启动。本机重新检查 C:/Users/A/Documents/FYP，start_gate_dc.sh（1056字节）、start_gate_genus.sh（1059字节）、xzy01-gate-check-v1.zip（6150字节）及旧综合 ZIP 均存在，目录不是链接。不能将本机已写入等同于学校已可见；可能共享列表/路径状态变化，尚未证实原因。下一步只读列出学校实际共享目录，不重复启动、不重新综合、不要求新终端。

用户列出共享目录后，新入口和 ZIP 均可见，随后一次手动 DC gate-check 已真实执行。工作目录 `/staff/ee/smaap/xzy01-gate-checks/xzy01-gate-dc-20261015T032640Z-455c033f`。结果 **FUNCTION_FAIL：1840检查、302错误、仿真退出0**，nonce `e07fffacd15c44f98b148868058e6016`。不是 PASS，保留原始失败，不因退出0改变结论。

本机已收取自动白名单回传，ZIP SHA256 `8b9a0a255076a765836fd98783c6b09b7d9867481ce6a0dbcca4780196d2a16a`，15成员，CRC/hash/白名单通过，原始文件保存在 `workflow/gate-check/raw`，解压在 `workflow/gate-check/returned/<上述ZIP哈希>`。学校单元模型为 PDK `Front_End/Verilog/NangateOpenCellLibrary.v`，220307字节，SHA256 `7b80af03f2ed72d40f014b836b13526aff3f64105415587c74f2260588b74363`，只回传指纹，不回传模型字节。实际 Xcelium 23.03-s004，所有所用单元编译0错误；日志唯一编译警告 SPDUSD（include目录未使用）。日志无逐检查实际输出，不能定位302错误的根因。

下一步准备独立诊断版本：保持原网表、原固定测试、原 -nospecify 设置和学校单元模型，增加只读波形观察（无force或输入修改），新工作目录/nonce，不覆盖失败尝试。Genus 网表功能测试暂不推进，先诊断 DC。初步误算向量位权后已纠正：打包位为 rst_n[4]/data_in[3]/expected_pre[2]/expected[1]/valid_pre[0]；有效pre期望1为137、post期望1为139，不能由302错误数推断输出恒0。

DC 首次失败回传进一步复核：runner、manifest、输入锁、TB、向量与 v1 包逐字节一致；网表哈希正确，独立回执解析重现 FUNCTION_FAIL。摘要 `workflow/gate-check/dc-first-functional-review.json`。

诊断 v2 已放共享目录：`start_gate_dc_diag.sh` 和 `xzy01-gate-diag-v2.zip`，ZIP SHA256 `ce508dbff84e8411f8ef473ef932aff88724d8b1eac42d35520741651aa7218b`，发布记录 `workflow/gate-check/release-diag-v2.json`。只增加 -access +r 和 bind 观察模块记录 tb 与 tb.dut 一级信号到 diag.vcd，不包含商业库源码，不改变原测试/网表/仿真时序选项。仍一次手动 DC 仿真、180秒上限，不自动循环。3项离线测试再次通过、bootstrap/runner Python3.6语法及ZIP CRC通过；学校诊断尚未执行。新入口命令先列出共享目录刷新可见列表，再启动同目录脚本，合为一次粘贴。

v2 真实诊断回传：学校目录 `xzy01-gate-dc-20261015T033043Z-5035ca4e`，1840 checks / **300 errors**，nonce `9b9238db21c648778c8eb3b7bb80f290`，退出0。ZIP SHA256 `ac3516a6d001292c9d3bb7899d5a08b7a93437a071961aff7cf6433c21a467b9`，17成员，CRC/hash/白名单通过；原 ZIP/JSON 与波形均保存在 workflow/gate-check/raw、returned。观察器改变后错误数302→300，提示可能与调度相关，不能以此判定设计原因。

波形证据：1ps单位；t=1999ps rst_n=0、clk=0 时，state/输出/QN连线仍有X；t=9999ps state=000、n2=n4=1，但 n3=X，与 state[1]=0 的互补输出不一致。后续时钟反复传播X。当前证据支持检查学校单元UDP调度/初始化语义，不足以宣称网表功能正确。VCD包含 tb与dut信号，未导出商业库源文件。

Cadence 官方 Gate-Level Simulation Methodology 第6页提供 -sequdp_nba_delay（14.2起支持），将时序UDP输出放在NBA区域以避免零延时竞争，且不添加实际非零时延。下一受控版本仅在 v2 命令增加该选项，保留观察、原网表、原TB/向量、-nospecify及模型指纹。不使用会隐含全局delay_mode_zero的 -seq_udp_delay，以免改变固定TB激励；不强制状态或删减失败用例。此为待验证假设，旧失败保持。

v3 已准备到同一共享目录：`start_gate_dc_nba.sh`（固定DC）、独立Genus入口暂不操作、`xzy01-gate-nba-v3.zip`（6520字节），SHA256 `a4d10671d7d79c7a2c67acd1b3ec8868ba33e96337143fb68e86a58781bde34e`；发布记录 `workflow/gate-check/release-nba-v3.json`。新runner/boot Python3.6 AST兼容、ZIP CRC与3项离线回归通过；学校v3尚未运行，不能预判修复成功。

v3 真实运行仍1840 checks / **300 errors**，nonce `95155aecb47045128c1943b3804e3d6d`；学校目录 `xzy01-gate-dc-20261015T033403Z-f3099832`。原始回传ZIP SHA256 `147b3334e7ab98c6754fdff8a1d8207ab5ca3bc9c0b301a8e562b99381f7e87e`；已校验CRC/hash/白名单并本机保存。实际命令确认含 -sequdp_nba_delay，未解决失败，不能继续据此声称调度问题已修复；暂不追加学校参数试跑。

随后从公开 FreePDK45 源库 Gitiles 下载公开版本（不是从学校上传）：https://foss-eda-tools.googlesource.com/third_party/freepdk45/+/954b16e2fcd52994e9d3c8b5af35b5f91d261889/Front_End/Verilog/NangateOpenCellLibrary.v?format=TEXT 。公开文件220307字节，SHA256 `7b80af03f2ed72d40f014b836b13526aff3f64105415587c74f2260588b74363`，与学校模型指纹完全一致，允许本机对同字节模型进行诊断，无需上传学校库。仅保存在Git忽略的 workflow/gate-check/public-library/，不加入回传或提交。

模型静态发现：非NTC分支中 ng_xbuf 对 RN 等输入反向驱动，ng_xbuf 在 i=X 时输出1；TETRAMAX 条件分支禁用这些输入驱动实例。该输入驱动可能与外部输入产生多驱动解析，是否是本次根因待本机同字节模型的正/负对照验证，不直接修改学校库，也不先判功能通过。

本机同字节公开模型的实际 Icarus 对照（不计学校结果）：默认分支在原DC网表/原TB/原向量下1840 checks /300 errors，复现学校错误数；仅加 -DTETRAMAX 后1840/0。模型自带 TETRAMAX 宏禁用 ng_xbuf 输入反驱动实例，逻辑门与触发器功能仍由原模型提供，并非调用TetraMAX工具。负对照在独立网表副本额外驱动输出0，TETRAMAX下仍检出330错误，表明没有关闭固定判题或屏蔽功能错误。冻结网表/原RTL/学校库均未改。

Genus本机同配置初查1840/0，但首次副本以read_text/write_text生成，因Windows换行转换导致网表字节哈希不同；该结果仅作同文本初查，下一步另建字节精确副本复核并保留该记录。全部对照证据 `workflow/gate-check/local-model-controls.json`；各目录保留编译/仿真日志和回执。

拟准备v4学校功能模型配置：从v2诊断配置仅增加 +define+TETRAMAX，不叠加已无效的NBA选项；保持原模型字节/网表/固定测试/观察器，执行记录明确保存宏。必须等待真实学校1840/0回传才判断该学校配置通过；历史302/300/300错误结果不得覆盖。

Genus字节精确本机复核完成：netlist SHA256 `24a9fe2f270033a5bf29a2f7f2f4e7e9a39337c63ce6788a182f574a2bc1fd2b`，原TB/向量/同字节公开模型，实际Icarus +TETRAMAX 得1840/0；原换行归一化初查保留且不作为字节绑定依据。DC本机原样+宏1840/0，负对照330错，根因链比单纯更换参数更有依据；学校Xcelium新配置仍待验证。

v4 已准备共享入口 `start_gate_dc_functional.sh`（DC独立）、Genus独立入口备用。包 `xzy01-gate-functional-v4.zip`，6805字节，SHA256 `e4833e903a0e59c69795665641381e17bc590d65d3910eece18e2b1c0752a9b3`，发布记录 `workflow/gate-check/release-functional-v4.json`。模型宏仅允许已校准哈希7b80af...74363，若学校模型字节不同则停止。3项离线测试、Python3.6 AST、ZIP CRC和共享复制完成；新版本不包含公开或学校单元库字节。下一学校操作仅运行DC功能分支入口，自动回传，不启动Genus或重新综合。

## DC 学校综合网表固定功能测试通过（v4）

用户单独运行 start_gate_dc_functional.sh，学校目录 `/staff/ee/smaap/xzy01-gate-checks/xzy01-gate-dc-20261015T034405Z-78818c9a`；回执 `RTL_LAB_V1 724a807172574606943b923b9f8f0208 checks=1840 errors=0`，Xcelium退出0，实际23.03-s004。回传ZIP SHA256 `07ac6f84aa43a21a680ffe514552fcd4e4d06a4a971936497560ace88325f23a` 已CRC/hash/白名单核验、原 ZIP/JSON本机保存。

本机审阅确认：runner/manifest/输入锁/TB/向量与v4包逐字节相同，DC网表哈希与本次综合产物相同，来源记录匹配，模型哈希固定，model_defines=[TETRAMAX]、nba_sequential=false，原始xrun日志实际含 +define+TETRAMAX。完整nonce/检查数/零错误/退出码独立复核通过。摘要 `workflow/gate-check/dc-functional-v4-review.json`；解压证据 `workflow/gate-check/returned/07ac6f84aa43a21a680ffe514552fcd4e4d06a4a971936497560ace88325f23a/`。

当前DC功能结论升级为 **FIXED_TEST_PASS：同一固定1840检查下的综合网表功能已验证**，范围是原模型TETRAMAX分支、无SDF、-nospecify配置，不是全输入形式等价或时序验证。旧三次失败保留为默认模型分支配置失败，与本机可复现输入反驱动问题相符；不修改旧记录。DC已知3条hold违例/复位释放边界继续保留。下一步单独运行Genus同配置功能入口。

## Genus 学校综合网表固定功能测试通过；本轮功能阶段完成

用户单独运行 start_gate_genus_functional.sh，工作目录 `/staff/ee/smaap/xzy01-gate-checks/xzy01-gate-genus-20261015T034758Z-33ccf023`；回执 `RTL_LAB_V1 c62faa07394a431683dec8e659235102 checks=1840 errors=0`，退出0，实际 Xcelium 23.03-s004。ZIP SHA256 `442775f362e0c6079fcf0ff0fdee305eb2257e42f332d791cd91c319fe06926c`，CRC/hash/成员白名单核验通过并回收原ZIP/JSON。

原始回传审阅通过：runner/manifest/输入锁/TB/向量与v4包逐字节一致，Genus网表哈希 `24a9fe2f270033a5bf29a2f7f2f4e7e9a39337c63ce6788a182f574a2bc1fd2b` 与原综合产物一致；包来源/nonce/固定模型指纹/实际 +define+TETRAMAX/no-NBA 配置核验通过。独立解析确认1840检查、0错误、仿真正常退出；两份学校成功证据的全部文件哈希再次核对通过。

### 最终功能与时序状态（替代上文早期“网表功能未验证”状态）

| 层次 | DC | Genus |
|---|---|---|
| 学校真实综合、产物回收、报告审阅 | 已完成 | 已完成 |
| 学校综合网表固定功能测试 | FIXED_TEST_PASS，1840/0 | FIXED_TEST_PASS，1840/0 |
| 功能配置 | Xcelium23.03-s004 / Nangate原模型TETRAMAX分支 / -nospecify / 无SDF | 同左 |
| 时序 | 3条hold违例，最差-0.07ns，未闭合 | hold未报告，证据不足 |
| 全输入形式等价、复位释放时序、完整多角签核 | 未执行/未覆盖 | 未执行/未覆盖 |

原始默认模型配置失败302/300/300全部保留；本机同字节模型复现和负对照证据均保留，不把本机结果计为学校成功。本轮没有改原RTL、综合网表、测试台/向量或学校库文件，没有新增模型调用、SSH/学校循环批处理、关机或上传库/许可证。

证据索引：

- 校验后的精简成果：`evidence/ece-mapped-functional-20261015/summary.json`、dc-result.json、genus-result.json、evidence-lock.json；只含结果、指纹、配置与适用范围，无库源码或完整商业日志。
- 详细审阅：`workflow/gate-check/dc-functional-v4-review.json`、`genus-functional-v4-review.json`。
- 完成凭据：`workflow/gate-check/school-functional-final-20261015.json`。
- 原始学校ZIP/JSON与所有失败尝试：`workflow/gate-check/raw/`；解压日志与波形在 returned/<各ZIP哈希>/；均为Git忽略的本机私有证据。

用户要求的本轮两工具综合网表固定功能验证已完成，无需再输入学校命令。后续若继续时序阶段，应另立约束覆盖/Genus hold诊断任务，保留当前功能通过和DC hold失败，不将两类结论混合。未向其他对话自动发送消息；总控可直接读取本记录与精简JSON。

## 2026-10-16 新实验规则同步（仅记录，未执行）

已读更新后的 AGENTS.md、FYP_FIXED_INPUT_RTL_RULES.md、validation/R1BC_RULE_REVIEW_20261016.md。新主线由探索对话独占准备/执行，总控审核冻结有限方案后单次放行；本综合对话不重复建批或调用模型，不启动综合/学校任务，不改总控计划、AGENTS 或其他对话目录。fyp 自动化保持暂停，本次未触碰其状态。

后续综合材料须遵循：同题原规格/接口/输入/固定向量/测试台/参考/既有事件流原字节保持；三候选模型 gpt-5.6-luna、gpt-5.6-terra、gpt-5.6-sol 的实际完整提示词（system/user/包装/顺序）逐字一致；主线为原规格→一次调用→RTL，无前置计划/IR、候选IR、反馈、私有测试或人工RTL修复。相同样本数/调用机会/输出预算及共同设置，模型请求身份与实际token消耗/身份局限分列，不静默换模型、补样或扩批。固定测试、有界SAT和事件/复位验证使用一致分母，失败/不支持/未执行如实单列；额外反例只另存诊断，不回写原输入或提示词。

**本对话已完成的学校单例属于历史 IR 辅助来源**：paired-a32 / m01__real_overlap__s001__control。control 不含反馈，不等于不含候选IR；不得重新标作本次“纯规格、单次直接RTL”新基线。该例的两工具综合及各1840/0综合网表功能结果继续有效，但只说明此历史样本的工具链/固定功能验证，不证明新三模型实验正确率或方法收益。历史原RTL、提示词、综合网表、失败/成功证据和时序缺口均保持，不重新生成或追溯改分。

R1b/R1c 来源核查仅作为历史附加验证背景：24/64两个选择集合重叠，候选IR/反馈和两阶段来源需区分，不能合并成88个独立设计，也不能整批视作新主线直接RTL基线。本记录仅同步用户规则，没有新增模型/仿真/SAT/综合/学校运行、采购或对外消息。
