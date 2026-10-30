# 30候选有限准备审核材料

建议先审独立的 **36槽主候选包**：Prob055_conditional、Prob124_rule110、Prob072_thermostat × 3模型 × 有/无RAG × 2样本。此为待审方案，尚未执行或放行。

- [主候选36槽清单](console-package-main36.json)：max_calls=36，保持原请求字节和槽ID，仅连续重编号。
- [300槽归档草案](console-package.json)：25题×12，其中36主候选机会、264辅助机会；不得将口头36许可用于此300槽包。辅助题没有自动执行授权。
- 总分母30题：3主候选、22辅助、5不得执行；360为筛选时最大机会数，不需凑满。
- [30题完整原文](ORIGINAL_PROMPTS.md)、[逐题审阅与行号证据](reference-risk-review.json)、[补充说明](review-addendum.json)、[离线核验](offline-package-audit.json)。

## 取材、方法与时间线

现有已采用20题，加冻结剩余顺序21—30，共30题。scope.json在新增正文读取前冻结；未按检索命中或预期成绩选题。90源文件中60复用旧缓存，30次公开GET取得新增10题文件，0重试。Git blob与SHA256逐一核对；来源NVlabs/verilog-eval固定commit c498220d0a52248f8e3fdffe279075215bde2da6，MIT许可。官方仓库来源不等于逐题作者已核实，也不证明模型训练未见。

RAG完全复用已冻结的48段TF-IDF A包（14文件相同），lowRISC固定commit 9c15ff5dce23eef969e00ab3715153967419eadd，CC-BY-4.0。A旧封存2026-10-24 07:00:39 UTC早于旧B首次读题07:00:59 UTC。每题仅调用原检索器一次，保留全部48排名、命中词贡献、top3、上下文；30题均非空命中。这不代表资料有帮助。未调库、词表、参数、排名、片段或包装，也未调用embedding。

原题全文原字节保留，中文解释独立。同题同条件三模型及两样本的system/user内容完全相同；有RAG仅追加冻结上下文。参考和TB未拼入消息。旧20采用记录与历史/近重复标签完整保留，本轮分类不倒改旧采用决定或成绩。

## 参考校准与保留的失败

本轮恰好30次Icarus编译、30次vvp仿真，未重跑：仅在独立dut.sv中将参考模块名改为TopModule，原参考和TB不改。原始日志全部退出0、无超时，零失配且检查数为正。这仅证明同源参考别名在原TB下自洽，不能证明参考独立正确、覆盖完整或真实生成RTL通过。

首版回执解析器未处理Windows CRLF，30个result.json均误报SIMULATION_OR_RECEIPT_FAILURE。这些误报、日志及源码全部保留；receipt-audit.json只读解析现有日志纠正计数，0重跑。编译警告仍保留。旧默认代理回归的3 failure/1 error保留，不重测。原题时钟双边沿active区比较、NBA采样与参考X屏蔽等限制仍存在；学校检查数可能不同，不能以本机计数回填旧成绩。本轮学校工具执行0。

## 模型、预算及解释边界

|OpenRouter ID|角色假设|冻结参数|
|---|---|---|
|openai/gpt-4o-mini|较小/较旧候选|不发送reasoning/temperature/seed|
|openai/gpt-4.1-mini|第二能力档候选|不发送reasoning/temperature/seed|
|openai/gpt-5.6-luna|5.6对照|reasoning.effort=medium|

三个ID来自10月24日已保存的OpenRouter公开目录/端点GET；本轮复用快照，新增目录GET与账户探针均0。固定provider only=[openai]、allow_fallbacks=false、require_parameters=true。公开目录支持参数不证明当前账户/路由可用，未知保持UNKNOWN。较小、较旧不等于已证实RTL较弱；不同架构、训练和推理预算也是混杂因素，不能把差异单独归因为模型新旧。

预算calls_only：36槽推荐待审，300槽仅归档；无8192或其他token cap字段，不设美元硬上限。manifest的max_tokens=null只是记账，实际请求不含此字段。模型/embedding调用0，尚无usage账单，cost=null不能解释为未来免费。若后续获准执行，应保留实际输入/输出/推理/cache token、费用与缺失值；未知调用不重发，错误与负结果不补样。

比较每模型Δ=同题RAG通过率−无RAG通过率，再比较Δ的模型间差异；同时报告帮助、损害、不变和未完成。按题配对，不能把同题重复样本当独立题。主候选仅3题，结论只能是探索性；22辅助应另列，近重复题族不能冒充独立新题。没有收益也保留，不据结果调RAG或补题。

## 控制台审核边界

绑定console v3 recovery-r1现行13文件锁，bridge SHA为492bb008b8d42c524a9241ea437ecb9b89f004cc9a1a08028687f69ec12816f5。两个清单均通过真实console_cli_v3 preview，全部NOT_STARTED；预览时网络、子进程、transport和dispatch被禁止。没有调用学校或生成后处理，没有建立模型运行状态。

DRAFT_REVIEW字段本身不是技术执行门。执行还必须有绑定清单SHA、源码、模型及全部槽ID的独立release；本包无release。36包和300包是重叠方案，不能同时放行，否则会重复调用同一批主候选。用户仍需审阅原题、三个模型组合及无费用硬上限的预算；本材料不构成执行授权。

旧155项证据/控制台绑定及本轮14个A文件在封包核验时未变。总控另存input-audit.json独立核90源与30组日志；本包未修改总控审计文件。有限准备到此结束，不新增实验。

## 30题分母

|序号|题目|分类|原回执检查数|检索片段|
|---|---|---|---:|---|
|1|Prob055_conditional|MAIN_CANDIDATE|112|GEN023, GEN021, GEN048|
|2|Prob142_lemmings2|AUXILIARY|441|GEN023, GEN043, GEN021|
|3|Prob124_rule110|MAIN_CANDIDATE|6283|GEN022, GEN023, GEN021|
|4|Prob016_m2014_q4j|AUXILIARY|100|GEN023, GEN041, GEN021|
|5|Prob135_m2014_q6b|DO_NOT_EXECUTE|100|GEN043, GEN023, GEN048|
|6|Prob026_alwaysblock1|AUXILIARY|219|GEN023, GEN021, GEN043|
|7|Prob139_2013_q2bfsm|AUXILIARY|1002|GEN043, GEN019, GEN044|
|8|Prob020_mt2015_eq2|AUXILIARY|2000|GEN023, GEN021, GEN019|
|9|Prob112_always_case2|AUXILIARY|94|GEN023, GEN048, GEN047|
|10|Prob010_mt2015_q4a|AUXILIARY|202|GEN023, GEN021, GEN019|
|11|Prob108_rule90|AUXILIARY|7121|GEN022, GEN021, GEN043|
|12|Prob140_fsm_hdlc|AUXILIARY|801|GEN019, GEN044, GEN021|
|13|Prob137_fsm_serial|AUXILIARY|905|GEN043, GEN047, GEN021|
|14|Prob129_ece241_2013_q8|AUXILIARY|440|GEN043, GEN023, GEN019|
|15|Prob153_gshare|DO_NOT_EXECUTE|1083|GEN021, GEN043, GEN044|
|16|Prob048_m2014_q4c|AUXILIARY|100|GEN022, GEN023, GEN047|
|17|Prob116_m2014_q3|DO_NOT_EXECUTE|100|GEN023, GEN021, GEN022|
|18|Prob025_reduction|AUXILIARY|100|GEN021, GEN019, GEN023|
|19|Prob138_2012_q2fsm|AUXILIARY|400|GEN023, GEN022, GEN047|
|20|Prob130_circuit5|DO_NOT_EXECUTE|141|GEN023, GEN048, GEN022|
|21|Prob011_norgate|AUXILIARY|219|GEN023, GEN021, GEN019|
|22|Prob013_m2014_q4e|AUXILIARY|100|GEN023, GEN021, GEN019|
|23|Prob107_fsm1s|AUXILIARY|230|GEN023, GEN043, GEN021|
|24|Prob072_thermostat|MAIN_CANDIDATE|248|GEN023, GEN021, GEN037|
|25|Prob090_circuit1|AUXILIARY|120|GEN023, GEN022, GEN021|
|26|Prob069_truthtable1|AUXILIARY|58|GEN023, GEN021, GEN019|
|27|Prob133_2014_q3fsm|AUXILIARY|1414|GEN043, GEN044, GEN023|
|28|Prob128_fsm_ps2|AUXILIARY|400|GEN043, GEN019, GEN047|
|29|Prob053_m2014_q4d|DO_NOT_EXECUTE|100|GEN023, GEN021, GEN047|
|30|Prob058_alwaysblock2|AUXILIARY|219|GEN043, GEN023, GEN019|

## 1. Prob055_conditional — MAIN_CANDIDATE

四个8位无符号数取最小值。

契约：ref先min=a，再依次与b/c/d比较并替换；循环不变式为已访问元素最小值，最终覆盖四项。相等返回相同数值；0/255边界无需特殊处理，无时钟/reset。

历史/近重复：比较器原语相关，但不是原二输入比较标志功能；保留旧条件纳入及已读标签。

原测试覆盖：原TB五组定向最小位置及100随机边沿，未声明穷举32位输入。

[prompt.txt](originals/dataset_spec-to-rtl/Prob055_conditional_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob055_conditional_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob055_conditional_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob055_conditional_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob055_conditional_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob055_conditional_test.sv)

- prompt.txt SHA256 `a4cb1a6391988c0c0661808b8bafb625160c70dab00c917bc970be65aa9b34c7`；Git blob `1e002f2d4e003b77db9fa42e1ca8c8013b4465b4`
- ref.sv SHA256 `2df6d288e7b4439de40d0225546cf1df4a17075bd577a73e6faf25f0ba6d0a2d`；Git blob `831e6502110f082ab23588d9d4f1dab9dd00825d`
- test.sv SHA256 `01b9ae5a9b87c2349c37fb9bd616a63c9da460fd672e9ae8aedc8f2c378a7909`；Git blob `afe12939e1dc64f96be7cc064b916196050e2907`

[完整排名及命中词](retrieval/Prob055_conditional.json) · [实际上下文](contexts/Prob055_conditional.txt) · [原始仿真回执](calibration/Prob055_conditional/simulate.json)

## 2. Prob142_lemmings2 — AUXILIARY

行走/坠落记方向四状态Moore机。

契约：1位控制，2位state；posedge clk，posedge areset异步优先WL。WL/WR先判断ground，故落地/离地与bump同周期均不改方向；FALL状态忽略bump。双bump按当前方向翻转，符合文字。非法state缺default，非复位前有效契约。

历史/近重复：保留Prob127/155行走坠落实质重叠。

原测试覆盖：原TB含异步reset_test、定向坠落及400次随机，不能证明所有半周期变化均覆盖。

[prompt.txt](originals/dataset_spec-to-rtl/Prob142_lemmings2_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob142_lemmings2_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob142_lemmings2_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob142_lemmings2_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob142_lemmings2_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob142_lemmings2_test.sv)

- prompt.txt SHA256 `dff9caac89ffa86372042cda54ca68f8388a2ca4f33f20092c3ef1db904bf466`；Git blob `cdc4ffea943c2c4f2f018b1bc71d9804eaf37f4e`
- ref.sv SHA256 `d12d0d89d1ca10c260297a0b5e01e619272eb817d3aa18da9528008d9a34db70`；Git blob `7ab9861633d63b3e48576a491dc149c769f8e764`
- test.sv SHA256 `b5c82af5e3d74789a715c6c57d9f0f29020cf59d408978dc8ffae8bc471f37cf`；Git blob `0f2b24e942cf38dfa145497ea9ad9569f9c58880`

[完整排名及命中词](retrieval/Prob142_lemmings2.json) · [实际上下文](contexts/Prob142_lemmings2.txt) · [原始仿真回执](calibration/Prob142_lemmings2/simulate.json)

## 3. Prob124_rule110 — MAIN_CANDIDATE

512位Rule110元胞自动机。

契约：posedge、load优先、无reset；ref为NOT(111或000或100)，逐三元组与原8行真值相符。左邻q[511:1]在512位按位表达式零扩展，右邻拼0，边界为0。初态未加载前不约束。

历史/近重复：保留旧条件纳入；与108同接口/加载/边界结构相关，不把两题作独立族。

原测试覆盖：原TB加载bit0、bit256、4df、随机及连续load后演化；$random只有32位来源，非512位均匀覆盖。

[prompt.txt](originals/dataset_spec-to-rtl/Prob124_rule110_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob124_rule110_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob124_rule110_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob124_rule110_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob124_rule110_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob124_rule110_test.sv)

- prompt.txt SHA256 `3149f58c7fa9a5c9ac21216994a268ea5b143a9c0cd56872f8ea7835f10ecdd3`；Git blob `559ee5d2b9b16d978a6b6f76d5d984707d04c211`
- ref.sv SHA256 `c95a474c70bb071b1b8adc0c23a86822928a2c7cb20fde28b8e48cd6a19aad81`；Git blob `fb453ffac073c5ecc49c69c799b6cb04f2b68716`
- test.sv SHA256 `4099c733852aa603ff4ff244eb49d0712edd2df0834d68d6f827700a5ad57f00`；Git blob `25d993717a7ff4d8b5148580efb9d421251f2353`

[完整排名及命中词](retrieval/Prob124_rule110.json) · [实际上下文](contexts/Prob124_rule110.txt) · [原始仿真回执](calibration/Prob124_rule110/simulate.json)

## 4. Prob016_m2014_q4j — AUXILIARY

4位加法含第5位进位。

契约：x/y unsigned4，5位上下文加法保留最大15+15=30。无时钟/reset。ref用加号而非显式全加器；功能TB不能验证必须full adders的结构要求。

历史/近重复：保留adder8/加减器宽度变体标签。

原测试覆盖：原TB100随机，不保证穷举256对。

[prompt.txt](originals/dataset_spec-to-rtl/Prob016_m2014_q4j_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob016_m2014_q4j_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob016_m2014_q4j_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob016_m2014_q4j_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob016_m2014_q4j_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob016_m2014_q4j_test.sv)

- prompt.txt SHA256 `bdc58ca32db81e53addd16cc5cd671c2d1f839591317ebe7174fb16b9ec23dc5`；Git blob `eb17847fe7f660baf26ce23f3da293f292081ada`
- ref.sv SHA256 `dbfde2547444cd93dd259aa37ac84ae811e0bf36c656c404594129d5683d536c`；Git blob `75769c87a25d5e8610894c23d6f6a79da0732538`
- test.sv SHA256 `1e75d8de66fd70710909918fa2560737f4f260d7cfd131ec14491ff2ee679f88`；Git blob `8bce5176c055780863b35e06da51e52c5cf67d0f`

[完整排名及命中词](retrieval/Prob016_m2014_q4j.json) · [实际上下文](contexts/Prob016_m2014_q4j.txt) · [原始仿真回执](calibration/Prob016_m2014_q4j/simulate.json)

## 5. Prob135_m2014_q6b — DO_NOT_EXECUTE

六状态机的y[1]下一状态组合逻辑。

契约：ref case({y,w})覆盖12个合法组合，与转移图下一状态bit1一致；非法110/111返回X。原文同时说next-state和output Y1 is y[1]。例如y=001,w=0，下一C=010应1，而当前y[1]=0，存在可见冲突。无clk接口。

历史/近重复：保留原关键契约歧义；与138反相输入图同构。

原测试覆盖：原TB随机含非法state，参考X屏蔽比较，不修正文案。

[prompt.txt](originals/dataset_spec-to-rtl/Prob135_m2014_q6b_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob135_m2014_q6b_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob135_m2014_q6b_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob135_m2014_q6b_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob135_m2014_q6b_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob135_m2014_q6b_test.sv)

- prompt.txt SHA256 `02da5df3fa54157b706f445bb1e6a0d078c9c90b7af01218e0567187bb4d9d2d`；Git blob `c4f57f414e3b97cb659bf6690c70fc46d1007153`
- ref.sv SHA256 `1982076dae0458a47cf365dee5d2a052fe2a2368de3799a4a0bb9dbdb4d6d9ee`；Git blob `cad2e31f69c1179202eb9c115bb5844f06c6049c`
- test.sv SHA256 `cfcf1d9435480e60ab22686b9203b2523e4136ccc1bb9a47adc3d175f1528ed9`；Git blob `0bacf90ad5dc672676dc0572d3217682d2178bac`

[完整排名及命中词](retrieval/Prob135_m2014_q6b.json) · [实际上下文](contexts/Prob135_m2014_q6b.txt) · [原始仿真回执](calibration/Prob135_m2014_q6b/simulate.json)

## 6. Prob026_alwaysblock1 — AUXILIARY

assign和always两路AND。

契约：两输出均a&b，1位组合全赋值；无reset、多hot含a=b=1输出1。语法结构仅静态ref满足，功能TB不能检查模型用了哪种语法。

历史/近重复：保留历史087 AND重复；与本轮090同AND功能。

原测试覆盖：原TB计数遍历及200随机边沿。

[prompt.txt](originals/dataset_spec-to-rtl/Prob026_alwaysblock1_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob026_alwaysblock1_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob026_alwaysblock1_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob026_alwaysblock1_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob026_alwaysblock1_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob026_alwaysblock1_test.sv)

- prompt.txt SHA256 `6eae7df079dcd42bd6dedd42895a6ca4dae7c52112a894c20b17b0febd071924`；Git blob `328a09dc4c75c2b7365a38f7260ab09b9d7f3724`
- ref.sv SHA256 `8c56a4c015ef90a231d4ed1ccd661696fed4cd6e123dc45fc768f187608d129a`；Git blob `cd930f15397d8408d3030ec3e3d57f40140d480a`
- test.sv SHA256 `a22407ed040fbae0318860a70409e5de3f8c324983fe5bd0d77e1912f4af6fbd`；Git blob `3263890b5c85dd6cf4ee9d2ff6ea164cb315a9ea`

[完整排名及命中词](retrieval/Prob026_alwaysblock1.json) · [实际上下文](contexts/Prob026_alwaysblock1.txt) · [原始仿真回执](calibration/Prob026_alwaysblock1/simulate.json)

## 7. Prob139_2013_q2bfsm — AUXILIARY

101后两周期检查y并锁定输出。

契约：同步低有效resetn优先A；A->B输出f一周期，后S0/S1/S10检测101；G1/G2窗口y成功进入P1否则P0，永久状态直到reset。S1遇1保持，允许前缀重叠。

历史/近重复：保留历史sequence101实质重叠及扩展控制的保守标签。

原测试覆盖：原TB随机reset/x/y；起始resetn在posedge用阻塞释放存在与state采样竞态。

[prompt.txt](originals/dataset_spec-to-rtl/Prob139_2013_q2bfsm_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob139_2013_q2bfsm_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob139_2013_q2bfsm_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob139_2013_q2bfsm_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob139_2013_q2bfsm_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob139_2013_q2bfsm_test.sv)

- prompt.txt SHA256 `fd660ca7619ae0a5d8ebf262aadb5cb44555d509b453cf5d630204618d0a9bba`；Git blob `5d8e17796751125be1651149ad3b81dd3d12acf7`
- ref.sv SHA256 `402d30bac3c3565f2b88cf78d76f8a80f0469df5594ffd2e8fac39f4008e0806`；Git blob `486631538dee98686ee49354c6110f0ab994ddf4`
- test.sv SHA256 `526bf9a0f7806389fbad89837515512a65bd628033563f7d6b077c277f0a68af`；Git blob `d7fea9b4fc863aab7641866ff67198cf9b24d5ea`

[完整排名及命中词](retrieval/Prob139_2013_q2bfsm.json) · [实际上下文](contexts/Prob139_2013_q2bfsm.txt) · [原始仿真回执](calibration/Prob139_2013_q2bfsm/simulate.json)

## 8. Prob020_mt2015_eq2 — AUXILIARY

两个2位数相等比较。

契约：unsigned2等号输出1位；16组合中仅00/00、01/01、10/10、11/11为1，无reset。X输入未规定。

历史/近重复：保留历史rt_comparator等值支路宽度变体。

原测试覆盖：原TB1000negedge期间随机取4位，非正式全覆盖证明。

[prompt.txt](originals/dataset_spec-to-rtl/Prob020_mt2015_eq2_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob020_mt2015_eq2_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob020_mt2015_eq2_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob020_mt2015_eq2_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob020_mt2015_eq2_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob020_mt2015_eq2_test.sv)

- prompt.txt SHA256 `07d916e51b5866b561cb5f9df738156e61eb5b517cd5b52cd3f92acfc4979113`；Git blob `206022944035f9e4fb91e5390259cca058165625`
- ref.sv SHA256 `3a6624ece9483f19d94f1b361e7d648cb359cf1b17b91e4836e9a72c7b6144ae`；Git blob `8ed2d3330ae2a6c8832f3958b96454e7c88778f3`
- test.sv SHA256 `b27e2225b77c163bec94e4bbf19c7fb5f110f8cb56bc7b7471720982ad3a2212`；Git blob `ec45cd0de56c08dc70468a833a070cbec6e53739`

[完整排名及命中词](retrieval/Prob020_mt2015_eq2.json) · [实际上下文](contexts/Prob020_mt2015_eq2.txt) · [原始仿真回执](calibration/Prob020_mt2015_eq2/simulate.json)

## 9. Prob112_always_case2 — AUXILIARY

4位低位优先编码。

契约：2位pos；0=>0，非零取最低置1下标，ref显式16行均符合；多hot如1010=>1，与例子强调最低位一致。无reset。

历史/近重复：保留encoder4优先方向变体旧标签。

原测试覆盖：原TB一热移位、16值递增及随机。

[prompt.txt](originals/dataset_spec-to-rtl/Prob112_always_case2_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob112_always_case2_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob112_always_case2_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob112_always_case2_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob112_always_case2_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob112_always_case2_test.sv)

- prompt.txt SHA256 `6a17eb818d48dab63be542a115dee4223fb7bd480ea9a2161ca8724aab15cc82`；Git blob `6ea912251461481315029da263373ceb750b99f9`
- ref.sv SHA256 `1381f5ab0ed243628965c0d2c89bd792f0455a6c9a8e3b113fa380e2590e94ec`；Git blob `cc20be4a2760ddde44ec071cb75253351a0bd4a0`
- test.sv SHA256 `baf60f2facbac768d2e6e88fbdd4eecd7b5061d5f58059cf8432fd5834463086`；Git blob `15b05d016ce8a8b3962bc476578cb37da2df7a5f`

[完整排名及命中词](retrieval/Prob112_always_case2.json) · [实际上下文](contexts/Prob112_always_case2.txt) · [原始仿真回执](calibration/Prob112_always_case2/simulate.json)

## 10. Prob010_mt2015_q4a — AUXILIARY

z=(x xor y) and x。

契约：布尔化简x & ~y，四行00/01/10/11输出0/0/1/0；ref与题逐字公式相同。无reset。

历史/近重复：保留019和087 out_anotb同功能。

原测试覆盖：原TB随机四组合。

[prompt.txt](originals/dataset_spec-to-rtl/Prob010_mt2015_q4a_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob010_mt2015_q4a_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob010_mt2015_q4a_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob010_mt2015_q4a_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob010_mt2015_q4a_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob010_mt2015_q4a_test.sv)

- prompt.txt SHA256 `ddff8d7fc684321656bfa87bc8c428cf7044d2a2e4de8dc4be1b2ec6d9f50281`；Git blob `8217f94e5d01e200d442d4f1a42fac3cdabc26e4`
- ref.sv SHA256 `f9d234ca574a9b0df09f733c0fc9d08b3ff52fe3dd019ec5ae66d2a7c10c00a6`；Git blob `a280acecd607d0e775079bcecfd6b1b8e51be49f`
- test.sv SHA256 `cac566cc2151a3442f886b2958080e7ca27ceae9c596d95bc63e3bdbab52b730`；Git blob `b1f97aedefda2f6a504ba78f8f02d9f5cfb50b4b`

[完整排名及命中词](retrieval/Prob010_mt2015_q4a.json) · [实际上下文](contexts/Prob010_mt2015_q4a.txt) · [原始仿真回执](calibration/Prob010_mt2015_q4a/simulate.json)

## 11. Prob108_rule90 — AUXILIARY

512位Rule90元胞自动机。

契约：posedge load优先；q_next[i]=q[i+1] xor q[i-1]，左511位零扩展、右拼0；两端虚拟邻居0。无reset，load前初值未规定。

历史/近重复：保留124轮内结构相关，局部规则不同不洗掉标签。

原测试覆盖：加载边界/中间单bit及长演化，未穷举512位状态。

[prompt.txt](originals/dataset_spec-to-rtl/Prob108_rule90_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob108_rule90_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob108_rule90_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob108_rule90_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob108_rule90_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob108_rule90_test.sv)

- prompt.txt SHA256 `4630998fdc4009e15dcac0712ac56392621eb01a24ef5de09417f99fcf9b1508`；Git blob `a54b434ef030530ac6574570043e0a0e8f4f6e57`
- ref.sv SHA256 `65419cbb139b74225b3d35c2c5c054034d082de3f5f9c00b7bb79d0b48d845db`；Git blob `f3d412386e722632226b18b3da355d7f8e8fb85b`
- test.sv SHA256 `298ebda07623c87b6ac77ab7d971e3670ab30e3e221ffc9b5029d4d31f13aa37`；Git blob `4ddc0b00752a4c9e99d21cf0014cb7bb844812a9`

[完整排名及命中词](retrieval/Prob108_rule90.json) · [实际上下文](contexts/Prob108_rule90.txt) · [原始仿真回执](calibration/Prob108_rule90/simulate.json)

## 12. Prob140_fsm_hdlc — AUXILIARY

HDLC连续1计数及丢弃/flag/error。

契约：同步高reset最后NBA赋S0覆盖转移；5个1后0进SDISC、6后0进SFLAG、7后1进SERR并保持至0，输出Moore完整周期。非法state给X。

历史/近重复：保留143同十状态转移图的历史暴露。

原测试覆盖：原TB800随机偏向1并随机reset，特定长串覆盖不由次数保证。

[prompt.txt](originals/dataset_spec-to-rtl/Prob140_fsm_hdlc_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob140_fsm_hdlc_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob140_fsm_hdlc_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob140_fsm_hdlc_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob140_fsm_hdlc_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob140_fsm_hdlc_test.sv)

- prompt.txt SHA256 `8cccb78555aa84398c381d96b7385e3eee9b34333b7bc5807e6afc38c216eead`；Git blob `7f8971165e3a31861d8d0a507ebede957e1d0d18`
- ref.sv SHA256 `3479ed45a237f4997354f47f7ac7fabd149346dcea6da5be7e6bfb9fd0c3453c`；Git blob `11cb7e88c7ec64a4b12b1f2e5e183aa164b885f5`
- test.sv SHA256 `382792d3e904af5f5189988368b299ea04604313a0325a70f0b442927a8a4dd9`；Git blob `e0690f1d0d0df9883d13b862e0523f0ae8e370f6`

[完整排名及命中词](retrieval/Prob140_fsm_hdlc.json) · [实际上下文](contexts/Prob140_fsm_hdlc.txt) · [原始仿真回执](calibration/Prob140_fsm_hdlc/simulate.json)

## 13. Prob137_fsm_serial — AUXILIARY

起始0、8数据、停止1的串行done。

契约：同步高reset到START；start检测后B0..B7八拍，STOP检查，DONE一拍且可立即收下个start；ERR等1后重启。1位流，无输出载荷。

历史/近重复：保留146串行数据接收控制骨架重叠。

原测试覆盖：原TB定向合法/错误停止与800随机；最小状态数未要求。

[prompt.txt](originals/dataset_spec-to-rtl/Prob137_fsm_serial_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob137_fsm_serial_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob137_fsm_serial_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob137_fsm_serial_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob137_fsm_serial_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob137_fsm_serial_test.sv)

- prompt.txt SHA256 `fe3610ac99739ba5073e7eee30fcf190dea64cfbd7d564398b45deadd987b826`；Git blob `57a638b79ed2451c488ffdf3d955a4b23176f79a`
- ref.sv SHA256 `5344c780c84e0360c6a5d86963b22ce411db7dbdb14058cc949fe0bdc76ffd4b`；Git blob `4284b9a8dfb5267b9bdc87d6ff33c7199f59521c`
- test.sv SHA256 `1b9efc2dc5f8ad922d052842021c79513b01460d6450c2a4393e3b49a68ee3b6`；Git blob `b3e691e592d3ef0ed161c4bed7a76ca13f5dbc6e`

[完整排名及命中词](retrieval/Prob137_fsm_serial.json) · [实际上下文](contexts/Prob137_fsm_serial.txt) · [原始仿真回执](calibration/Prob137_fsm_serial/simulate.json)

## 14. Prob129_ece241_2013_q8 — AUXILIARY

Mealy重叠101检测。

契约：negedge aresetn异步低reset到S；3态S/S1/S10。S10时z=x组合，S10遇1回S1保留重叠10101。输出会在边沿间随x改变，不能用Moore保持判据。

历史/近重复：保留sequence101同序列与139相关。

原测试覆盖：reset_test及定向重叠与400随机；原计分仍边沿active采样。

[prompt.txt](originals/dataset_spec-to-rtl/Prob129_ece241_2013_q8_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob129_ece241_2013_q8_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob129_ece241_2013_q8_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob129_ece241_2013_q8_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob129_ece241_2013_q8_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob129_ece241_2013_q8_test.sv)

- prompt.txt SHA256 `84b421b6b8b363ad0046d586dc5c5460a8d21e5e3994a78b2f0cdcdc9ee0d7c7`；Git blob `1b2695162c16d8df93b5cec8683099e00ec9aa37`
- ref.sv SHA256 `ec3cb4240ae0cccc86355da25ec423cb4375ff93764e24a9cc8f7112c6199a20`；Git blob `5d5bed4e64fd9d5c3df6b8721bbe9037b1fef978`
- test.sv SHA256 `11dab6d12974756c629976cadab848b37992c67f314e45c18c5dae3ccad2586c`；Git blob `49664bdadec8e0bc03986164cf357292acdc96a9`

[完整排名及命中词](retrieval/Prob129_ece241_2013_q8.json) · [实际上下文](contexts/Prob129_ece241_2013_q8.txt) · [原始仿真回执](calibration/Prob129_ece241_2013_q8/simulate.json)

## 15. Prob153_gshare — DO_NOT_EXECUTE

7位历史gshare预测器。

契约：7位PC/history xor索引128x2bit，饱和计数0..3；mis-predict训练后写history优先预测，读旧PHT符合NBA。ref异步reset把PHT=01、history=0，而原题未给这些值；invalid预测输出X也属ref选择。

历史/近重复：保留关键reset契约缺失；自比通过不能批准隐藏初值。

原测试覆盖：原TB训练/回滚/同周期优先定向加1000随机；valid=0数据用X，计分屏蔽。

[prompt.txt](originals/dataset_spec-to-rtl/Prob153_gshare_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob153_gshare_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob153_gshare_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob153_gshare_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob153_gshare_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob153_gshare_test.sv)

- prompt.txt SHA256 `dfac7601e96bdcfacd43944bfcdd5c5677a4d9a68f56532a0608b525f54c36b4`；Git blob `5f94cbf598181845574a0690fcdad07b8989f715`
- ref.sv SHA256 `12d54877b5d0a2e71bc084cbc79c8b68363d2a739b073969f7e2221da6b38a98`；Git blob `5e6fb76f114bfdfb52b3902392fd6ee06048c807`
- test.sv SHA256 `180dacd01c7cf4666c7488d8683faa7e22ce2b130a98fb59660cc7ac3a16a8f2`；Git blob `8569e186f32e0d4bef062c9475edbba3b34d8e7a`

[完整排名及命中词](retrieval/Prob153_gshare.json) · [实际上下文](contexts/Prob153_gshare.txt) · [原始仿真回执](calibration/Prob153_gshare/simulate.json)

## 16. Prob048_m2014_q4c — AUXILIARY

1位同步高reset DFF。

契约：posedge clk，r优先q=0否则d，复位前初态未规定；原ref符合。

历史/近重复：保留dff/dff8r宽度变体。

原测试覆盖：原TB100随机边沿，r随机，不能当独立异步reset检测。

[prompt.txt](originals/dataset_spec-to-rtl/Prob048_m2014_q4c_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob048_m2014_q4c_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob048_m2014_q4c_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob048_m2014_q4c_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob048_m2014_q4c_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob048_m2014_q4c_test.sv)

- prompt.txt SHA256 `01faebfe50b95f304c326dd2f7cdc3cd67c3210f69a2de3fe8df02b3edaffb05`；Git blob `6115d48f2e58d732f6ca8095a79811d18fa534ee`
- ref.sv SHA256 `f143bdbb4847f35b5baa02f4c8c0242fd244b3daaf1306edd57e2c2c1c5dd908`；Git blob `4e6e6a55c3344006ea1b0c6b1132c0c519d935f1`
- test.sv SHA256 `7d823cdc2b74f0ae6c4d13826c0a5da785a41d493c894cd90a3a7c3b606a7a38`；Git blob `488c8aa7b6bb2492b0e6f162c776a1bd867fe66a`

[完整排名及命中词](retrieval/Prob048_m2014_q4c.json) · [实际上下文](contexts/Prob048_m2014_q4c.txt) · [原始仿真回执](calibration/Prob048_m2014_q4c/simulate.json)

## 17. Prob116_m2014_q3 — DO_NOT_EXECUTE

带dont-care的四变量卡诺图。

契约：接口4位x即[3:0]，图标x[1]x[2]/x[3]x[4]涉及不存在x[4]；可能一基编号，但未明确映射。ref16项含X，不能替作者确定变量对应。

历史/近重复：保留关键索引契约歧义，不因ref自比通过解除。

原测试覆盖：原TB100随机，参考X项不判错。

[prompt.txt](originals/dataset_spec-to-rtl/Prob116_m2014_q3_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob116_m2014_q3_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob116_m2014_q3_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob116_m2014_q3_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob116_m2014_q3_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob116_m2014_q3_test.sv)

- prompt.txt SHA256 `9c40c9be5f741d9678898b4e27c58737aed85873059f258eb3027706515f46ed`；Git blob `9c4b7b36b1f2be12a6e5b6c4666c3dd38d2b7cec`
- ref.sv SHA256 `71fc30b8d528205b1d97db9c6c0eeec7f936dbda016ab7a4a0e28ad80533988d`；Git blob `54c3e9afdfe6de0a188c092c0eda3bcc1fd0e1a7`
- test.sv SHA256 `5cdd2e30a960e24c43b4c214db7f752a3c098b39dd17378035d59a234b6b7288`；Git blob `b960c3e9dd662f5801578ccc8510259982f440b4`

[完整排名及命中词](retrieval/Prob116_m2014_q3.json) · [实际上下文](contexts/Prob116_m2014_q3.txt) · [原始仿真回执](calibration/Prob116_m2014_q3/simulate.json)

## 18. Prob025_reduction — AUXILIARY

8位偶校验位。

契约：parity=^in，输入加parity后总1数为偶；8位无符号、无reset，全0/全1均0，单1为1。

历史/近重复：保留历史parity8同功能。

原测试覆盖：原TB100随机边沿，非256输入全穷举。

[prompt.txt](originals/dataset_spec-to-rtl/Prob025_reduction_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob025_reduction_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob025_reduction_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob025_reduction_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob025_reduction_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob025_reduction_test.sv)

- prompt.txt SHA256 `0734b084119e62e858a877d0cb729da5d28f503fcb40c93a5c82a6fa75051d2d`；Git blob `7a13913a7c4a9c57013d8c269ce108d1809b191e`
- ref.sv SHA256 `2c3ed80d11c32321cb8c416c36ab78514880592e99f20a53b794cdf0944240be`；Git blob `2285cf66daba02cd4a69829fb0f616003a128bfb`
- test.sv SHA256 `66a717ac9794a526f8d87e25b14b5a65669b3f52b6854a19651a42a9d6603895`；Git blob `0fbf77a1d55b8e7c79a3f7a5b670af0026d307c2`

[完整排名及命中词](retrieval/Prob025_reduction.json) · [实际上下文](contexts/Prob025_reduction.txt) · [原始仿真回执](calibration/Prob025_reduction/simulate.json)

## 19. Prob138_2012_q2fsm — AUXILIARY

六状态同步Moore机。

契约：posedge同步高reset到A；逐行6x2转移与题一致，E/F输出1。非法state给X。separate always结构原ref满足但功能TB不能证明生成结构。

历史/近重复：保留与135输入取反后同构图暴露及旧相关标签。

原测试覆盖：原TB200negedge随机reset/w，未定向声明初始reset，早期X可能被屏蔽。

[prompt.txt](originals/dataset_spec-to-rtl/Prob138_2012_q2fsm_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob138_2012_q2fsm_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob138_2012_q2fsm_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob138_2012_q2fsm_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob138_2012_q2fsm_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob138_2012_q2fsm_test.sv)

- prompt.txt SHA256 `118be360b0c8dea9915cf4520b01886243c6df6c9e2301ed66abf8b6eab04147`；Git blob `4d61d544ec7b049a9dc62bb85a070e98f7ef745e`
- ref.sv SHA256 `d4fc98953061961badc2b9fae62831f301f986b6ba1a963ece1c183ad4cd7808`；Git blob `758cd1ed244a04d4638f7cc10cae3b4a53cd2736`
- test.sv SHA256 `0d414aeee013f7392e60b05d529ba47a37f2c7b458abbdfb78d0b140c1f785af`；Git blob `463e0744db065eb18c1313a7a5a91f6e82913128`

[完整排名及命中词](retrieval/Prob138_2012_q2fsm.json) · [实际上下文](contexts/Prob138_2012_q2fsm.txt) · [原始仿真回执](calibration/Prob138_2012_q2fsm/simulate.json)

## 20. Prob130_circuit5 — DO_NOT_EXECUTE

由一组波形猜四路4位mux。

契约：ref c=0/1/2/3选择b/e/a/d，其余f；原波形只在a=a,b=b,d=d,e=e固定时扫c，常量b/e/a/d同样满足已示例。未唯一规定其余输入值行为。

历史/近重复：保留欠定契约，不能以常见题型替代规格。

原测试覆盖：TB实际另用12034/56078和随机输入超出原示例，故隐藏约束可影响成绩。

[prompt.txt](originals/dataset_spec-to-rtl/Prob130_circuit5_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob130_circuit5_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob130_circuit5_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob130_circuit5_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob130_circuit5_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob130_circuit5_test.sv)

- prompt.txt SHA256 `e60c6bc1414689917b8f7b58a24d59187c794e10dd6801069b60f096c76e1303`；Git blob `731b9beabe68c12d5d706b7171aa5d48cf124152`
- ref.sv SHA256 `ff30762866bbad676b81e88155ccfa397eb716030369dbb7e9f330a1e6e24867`；Git blob `49f6bb308e3750c989deed23eea478e47c556058`
- test.sv SHA256 `563235dca0961f0df34bf51c25dc703d3a0884245fd39e7018d6997df60cb28a`；Git blob `34b979b9c0652c4ccca04b60e77321099abd8426`

[完整排名及命中词](retrieval/Prob130_circuit5.json) · [实际上下文](contexts/Prob130_circuit5.txt) · [原始仿真回执](calibration/Prob130_circuit5/simulate.json)

## 21. Prob011_norgate — AUXILIARY

2输入NOR。

契约：1位组合out=~(a|b)，00=>1其余0；无reset。

历史/近重复：与22仅端口名不同；历史087 out_nor完整同功能。

原测试覆盖：计数遍历及200随机边沿。

[prompt.txt](originals/dataset_spec-to-rtl/Prob011_norgate_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob011_norgate_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob011_norgate_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob011_norgate_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob011_norgate_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob011_norgate_test.sv)

- prompt.txt SHA256 `0d5777800631b73e5922ccec5061f76321cabe9ad68b770d371bf3f26a51d505`；Git blob `6a4975ede97a20cdba41e4e7d9da0b7fd37ebb65`
- ref.sv SHA256 `7e159a8077f15779839547fe079d25ee534f87a8b4b63680ef1741bc4f262b3b`；Git blob `01c8070990a9549daa8dab3b61d6fa79063b17fc`
- test.sv SHA256 `8b65220685623967aef6e529331d6a2bf401a61f62f0b93153d4eea98c2d03f6`；Git blob `9bf163628a198202201b13c8de1ed985410835ed`

[完整排名及命中词](retrieval/Prob011_norgate.json) · [实际上下文](contexts/Prob011_norgate.txt) · [原始仿真回执](calibration/Prob011_norgate/simulate.json)

## 22. Prob013_m2014_q4e — AUXILIARY

2输入NOR（不同端口名）。

契约：1位组合out=~(in1|in2)，与21同四行真值；无reset。

历史/近重复：与21精确功能重复且历史087 out_nor暴露。

原测试覆盖：100随机边沿。

[prompt.txt](originals/dataset_spec-to-rtl/Prob013_m2014_q4e_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob013_m2014_q4e_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob013_m2014_q4e_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob013_m2014_q4e_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob013_m2014_q4e_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob013_m2014_q4e_test.sv)

- prompt.txt SHA256 `c4adcffee7da43aa1ec11ae8ba93095a5e34f1ffade2418c05f2a4ef3075d9a4`；Git blob `8f14b2b308958e1b94075b38ecf7a58501e3929f`
- ref.sv SHA256 `9dbd9a718fb163bbb60d876b23518c9eb8d211dfc5f891aac87920da3b5b36b0`；Git blob `43371efbe4e0949f25e67543d16a3ae3b2250466`
- test.sv SHA256 `084d74cb95eaa0adc2c33fa13fdb43a7bace3c5714bf98854a161f21d5812ea6`；Git blob `cd114078bc50d09ab601dd81aace9837301459ba`

[完整排名及命中词](retrieval/Prob013_m2014_q4e.json) · [实际上下文](contexts/Prob013_m2014_q4e.txt) · [原始仿真回执](calibration/Prob013_m2014_q4e/simulate.json)

## 23. Prob107_fsm1s — AUXILIARY

输入0翻转、1保持的二状态Moore机。

契约：同步高reset到B，out=1；state_next=in?state:~state。所有两个state和输入组合有定义。

历史/近重复：历史109_fsm1完全同转移/输出，只有reset异步改同步。

原测试覆盖：含reset_test(0)、定向输入及200随机。

补充审核说明（优先于旧摘要的简写）：Prob107_fsm1s：原题明确同步高有效复位，但未显式指定 posedge；参考采用 posedge。不能将参考的边沿选择写成原题已明确要求。维持 AUXILIARY，不修改原题、参考、检索、messages 或既有300槽清单。

[prompt.txt](originals/dataset_spec-to-rtl/Prob107_fsm1s_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob107_fsm1s_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob107_fsm1s_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob107_fsm1s_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob107_fsm1s_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob107_fsm1s_test.sv)

- prompt.txt SHA256 `9b7597650973057aba09bff1a801614fc9b4f31ed40d6d85e0396dc600abe4a8`；Git blob `f73b79abf0ddb99ed1af32c8fefbb6ab7dce3e56`
- ref.sv SHA256 `1d8b86049ccf6097e33d0b8f9aefb0c387e8e6eb5405c00e380ab10ece0fab0d`；Git blob `b31789e00e031722143d577fcff03d5a21fa7827`
- test.sv SHA256 `22536f340d4972cb797cabb252b6c8845c43b78e24b68db2540901d8a0b6752e`；Git blob `8cdc923d1c04c01fa056c2ab19d890bef687d16f`

[完整排名及命中词](retrieval/Prob107_fsm1s.json) · [实际上下文](contexts/Prob107_fsm1s.txt) · [原始仿真回执](calibration/Prob107_fsm1s/simulate.json)

## 24. Prob072_thermostat — MAIN_CANDIDATE

组合温控器及风扇。

契约：heater=mode&cold，aircon=~mode&hot；两者互斥，fan=heater|aircon|fan_on与ref三元式等价。mode/cold/hot/fan_on四输入共16行包括cold=hot=1均定义，无reset/锁存。

历史/近重复：共用mux/门原语，但带互斥制热制冷和风扇联动的整体接口未在冻结历史表发现同功能；已于本轮读取，不称训练未见。

原测试覆盖：冬夏定向覆盖同时hot/cold与fan_on，加200随机。

[prompt.txt](originals/dataset_spec-to-rtl/Prob072_thermostat_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob072_thermostat_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob072_thermostat_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob072_thermostat_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob072_thermostat_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob072_thermostat_test.sv)

- prompt.txt SHA256 `b99d5c7402c3d59b35c3396da199442e9fea075d0e31dd703b901ae97b445ae1`；Git blob `3cc5090aa7f538cc091e9ee224f7f1fe46fcc95c`
- ref.sv SHA256 `11ab9eccf4df5719e600eca68d15eafd612aecec668a0ff97951f5637d56fd1b`；Git blob `f1c64c971c91e5c6c6c144315105421dd14f3902`
- test.sv SHA256 `ff9b235a01aaabd6b13e085ef001b552de63dcb64a38e1f618672d740923ede3`；Git blob `08aba9e3deb54d54c953c32d5bd5a4d27581f69f`

[完整排名及命中词](retrieval/Prob072_thermostat.json) · [实际上下文](contexts/Prob072_thermostat.txt) · [原始仿真回执](calibration/Prob072_thermostat/simulate.json)

## 25. Prob090_circuit1 — AUXILIARY

波形完整真值的AND。

契约：原波形给出00/01/10/11全四组，唯一二值组合关系q=a&b；不因为waveform形式就判欠定。X/Z行为未要求。

历史/近重复：与本轮026及历史087 AND重复。

原测试覆盖：两次遍历4组合及100随机。

[prompt.txt](originals/dataset_spec-to-rtl/Prob090_circuit1_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob090_circuit1_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob090_circuit1_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob090_circuit1_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob090_circuit1_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob090_circuit1_test.sv)

- prompt.txt SHA256 `9ad1e640469124039c742f4486200880371f3d6ccf7736fbd7dc33791ccd3c49`；Git blob `d6b1b5bb86177513813d39bf28ed7e846bc37b4e`
- ref.sv SHA256 `9ed56f8134868536916665f10e183bdb3d931f3d05c3e68607b48c40ef6e020e`；Git blob `f2cedadd5bbafe1f60aacdfd7e662b0eec42ad52`
- test.sv SHA256 `855e27e7934c43660853b09c80101c064745f61662d9a1cba58353b4d2950020`；Git blob `77666866b0b7216e9f301dfad96eab2af765001f`

[完整排名及命中词](retrieval/Prob090_circuit1.json) · [实际上下文](contexts/Prob090_circuit1.txt) · [原始仿真回执](calibration/Prob090_circuit1/simulate.json)

## 26. Prob069_truthtable1 — AUXILIARY

三输入完整真值/单bit mux。

契约：8行f为0,0,1,1,0,1,0,1；ref为minterm2/3/5/7之和，化简f=x3?x1:x2，无reset。

历史/近重复：与历史022 mux2to1在sel=x3,b=x1,a=x2映射下完全相同；017为宽度变体。

原测试覆盖：原TB遍历8行；随后repeat(40)仅等待，随机赋值在循环外且紧接finish，不能称40随机向量。

[prompt.txt](originals/dataset_spec-to-rtl/Prob069_truthtable1_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob069_truthtable1_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob069_truthtable1_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob069_truthtable1_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob069_truthtable1_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob069_truthtable1_test.sv)

- prompt.txt SHA256 `2131087a44ad7f328bafcb1f1b0809c7ccaaaf6bdeca9b51398ef9203c705da2`；Git blob `3e7b635760ff8b5fb7f3e6156951268794e044f1`
- ref.sv SHA256 `4eb73956209794bdbb8b183514aa9cbd47ea71c54261c4a60fcebe2f8491af8b`；Git blob `cf5057cec12dc845dadce042f7ab041a5160ebc5`
- test.sv SHA256 `ab6e1284d378b2b640d1bac4608c17aab0e156d89868c665f22db9eff5a15cc1`；Git blob `364489114afe5cdc781bd7d3991d2ac38fd8ca7e`

[完整排名及命中词](retrieval/Prob069_truthtable1.json) · [实际上下文](contexts/Prob069_truthtable1.txt) · [原始仿真回执](calibration/Prob069_truthtable1/simulate.json)

## 27. Prob133_2014_q3fsm — AUXILIARY

每三周期恰好两个1输出脉冲。

契约：同步高reset到A，s只在A有效；B/C为分组边界，S10/S11记录第一位，S20/S21/S22记录前两位和；第三位使011/101/110进入C(z=1)。下一周期同时采下一组三位的首位，窗口不滑动。

历史/近重复：暂未见完全同功能历史，但与计数/FSM原语相关；原题as few states as possible不是功能TB验收项，本轮不声称最小化已证，因此辅助分析。

原测试覆盖：s持续1/再reset及随机脉冲；没有状态最小化结构检查。

[prompt.txt](originals/dataset_spec-to-rtl/Prob133_2014_q3fsm_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob133_2014_q3fsm_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob133_2014_q3fsm_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob133_2014_q3fsm_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob133_2014_q3fsm_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob133_2014_q3fsm_test.sv)

- prompt.txt SHA256 `b78ad94474c88f937088cdf4fb5a2c1aa83fcd065e20de3d3ed84f77f625bfbf`；Git blob `195f1737b1b1071d30131ecf38abddc5b87f4e55`
- ref.sv SHA256 `3c52c08d38debcd7e09092f2e7cf82e0497e058a9584ece479d1c3a4957afef1`；Git blob `bee3ee34c18cb975140949bafeb85f1618312507`
- test.sv SHA256 `7838cbe970c633be739f4ce7eb19d642baae7818068e05994acb802a94fd0c45`；Git blob `a85e9240118c93c3b8945fbdcb2d1a4876a60965`

[完整排名及命中词](retrieval/Prob133_2014_q3fsm.json) · [实际上下文](contexts/Prob133_2014_q3fsm.txt) · [原始仿真回执](calibration/Prob133_2014_q3fsm/simulate.json)

## 28. Prob128_fsm_ps2 — AUXILIARY

PS/2三字节边界检测。

契约：8位in仅看bit3找第一字节，之后两字节忽略bit3；第三字节后DONE一周期，DONE可直接接下一第一字节。同步高reset BYTE1。

历史/近重复：历史154_fsm_ps2data包含同一四状态done路径；本题仅删载荷输出。

原测试覆盖：200negedge随机输入/reset；未指定初始reset，初期X可能被屏蔽。

[prompt.txt](originals/dataset_spec-to-rtl/Prob128_fsm_ps2_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob128_fsm_ps2_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob128_fsm_ps2_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob128_fsm_ps2_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob128_fsm_ps2_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob128_fsm_ps2_test.sv)

- prompt.txt SHA256 `59ee508515a6b2113e46369feb8e4c34f7e71881a1c152ad6a722ee0ba560a0b`；Git blob `97a570339fe14735522fd8ea34e63be9b7a221db`
- ref.sv SHA256 `88fd53ff936047b70a0407ec1c4eb55d74d05a80ef4fa45997a288daae8d4d6d`；Git blob `da1884f62661c3febfb7527e31f3f126313c0aa2`
- test.sv SHA256 `03461424196e1d977774f4e603118291e3cccf0cfce1e693b3119833b6cb84a6`；Git blob `3b13764cf15c03f62c2f87ed58829bd2440defda`

[完整排名及命中词](retrieval/Prob128_fsm_ps2.json) · [实际上下文](contexts/Prob128_fsm_ps2.txt) · [原始仿真回执](calibration/Prob128_fsm_ps2/simulate.json)

## 29. Prob053_m2014_q4d — DO_NOT_EXECUTE

无reset的反馈XOR触发器。

契约：posedge out<=in xor out；原题明确无reset且不规定初态，ref额外initial out=0。合法未初始化寄存器与该ref会产生差异；不把initial写回题或据自比称规格一致。

历史/近重复：新增初态契约缺口，参考自一致不解除。

原测试覆盖：100随机边沿，TB未给初始化输入；参考起始0成为隐藏要求。

[prompt.txt](originals/dataset_spec-to-rtl/Prob053_m2014_q4d_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob053_m2014_q4d_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob053_m2014_q4d_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob053_m2014_q4d_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob053_m2014_q4d_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob053_m2014_q4d_test.sv)

- prompt.txt SHA256 `156b0927a00b17a96fef04c7bf2c331b5f8028aac9243115acad3a4473a4b6ef`；Git blob `df4eb7dccf202b3a5b7c51e43efafc0ac08c31d9`
- ref.sv SHA256 `2f78ec8c604efe45f02c1ed0715b79904767ecaead2e4abef29d6c96571e6537`；Git blob `ef0b791fae69abed41a878693a13621fc15fdfeb`
- test.sv SHA256 `7eb4635618b01419ae81123732b2126ca8677adc9f75a7fdf40852828f8da29e`；Git blob `a5a9c65900e42b67d5d55a68f0bc348440bd2892`

[完整排名及命中词](retrieval/Prob053_m2014_q4d.json) · [实际上下文](contexts/Prob053_m2014_q4d.txt) · [原始仿真回执](calibration/Prob053_m2014_q4d/simulate.json)

## 30. Prob058_alwaysblock2 — AUXILIARY

XOR的组合两路及寄存一路。

契约：1位a/b，assign和always_comb即时a xor b；out_always_ff在posedge采样，初态无规定，无reset。ref功能符合。

历史/近重复：与历史087 XOR/031 DFF及本轮026语法练习有关；三种指定语法结构不能由输出TB证明，保留辅助。

原测试覆盖：计数遍历加200随机，计分在双边沿，不能证明任意边沿间稳定性。

[prompt.txt](originals/dataset_spec-to-rtl/Prob058_alwaysblock2_prompt.txt) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob058_alwaysblock2_prompt.txt) · [ref.sv](originals/dataset_spec-to-rtl/Prob058_alwaysblock2_ref.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob058_alwaysblock2_ref.sv) · [test.sv](originals/dataset_spec-to-rtl/Prob058_alwaysblock2_test.sv) / [固定来源](https://raw.githubusercontent.com/NVlabs/verilog-eval/c498220d0a52248f8e3fdffe279075215bde2da6/dataset_spec-to-rtl/Prob058_alwaysblock2_test.sv)

- prompt.txt SHA256 `8332e8ca609d6e36cce74d514ec19ba122bfb23fa6c25d0242ba9f1dcc37bfbe`；Git blob `5bdee42327932f9bda672e4bee11910108fa8aa8`
- ref.sv SHA256 `392bc7b761c4c825747e1b85b0dcb9ebb37a6ef14844f807daf992ddd56bf7b6`；Git blob `b05e0f196375a24bfabe240fc92bd4657ffd5abb`
- test.sv SHA256 `2d1083d9cf01d4fa34d133995f31bd2da207256e67600f2283a9f584ba65cdb1`；Git blob `852f38ecf1d3a818ccc0cd1ff0d7db06b94e5e5a`

[完整排名及命中词](retrieval/Prob058_alwaysblock2.json) · [实际上下文](contexts/Prob058_alwaysblock2.txt) · [原始仿真回执](calibration/Prob058_alwaysblock2/simulate.json)
