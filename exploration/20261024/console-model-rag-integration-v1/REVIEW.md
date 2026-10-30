# 统一控制台接入审核材料

2026-10-24；状态：离线接入可审核，正式批次 BLOCKED_PENDING_SELECTION_AND_FREEZE。0 生成模型调用、0 embedding、0 学校工具启动；没有新增真实预约或 release。旧默认代理回归失败不重跑、不覆盖。

## 已完成与实际入口

旧 Open-Lab-v2.cmd、console_bridge.py、console_gui_v2.py、console_cli.py、console_school.py、console_school_runner.py 均未修改。旧窗口确实只接受 5.6 三模型，不冒充已支持新候选。

本目录 **Open-Console.cmd** 是同一控制台的独立版本入口：加载旧 GUI 的 Console 类及旧桥的 Package 基类，在独立模块实例中替换数据校验和学校传输按钮，复用原 dispatch、local_replay、school.pack、school.collect。没有第二套模型发送器、调度器或判题器，不改变已审 transport。新状态目录为本目录 runtime，不写旧 validation/console-openrouter-20261024-v1。读取历史336仅供只读展示。

本机打开方式：双击本目录 Open-Console.cmd；或使用本机 Python 以 `-B console.py` 启动。该入口使用既有 bundled Python 路径，其他机器需自行指定 Python 3.10+ 与 Tk；打开不联网。

验证导入步骤：点击“导入冻结包”，选择本目录 offline-preview/console-package.json。会显示 6 个合成槽位，覆盖 4o-mini、4.1-mini、5.6-luna 及两条件。它明确标为 OFFLINE_FIXTURE_NOT_EXECUTABLE，没有放行文件，不能运行。不要把它计为 20 题实验。gui-offline.json 是实际 Tk 导入记录（隐藏窗口测试，非人工视觉验收）。

## 独立版本控制

- 请求 ID 固定为 openai/gpt-4o-mini、openai/gpt-4.1-mini、openai/gpt-5.6-luna，现阶段仍为待用户确认组合。其他模型包括 Sol 不自动替换。
- 显式路由 OpenAI，禁 fallback，要求支持参数；只允许 system/user，禁止 tools/联网/插件及额外请求字段。Luna 显式 reasoning.effort=medium，另两模型无 reasoning；其余参数跨模型一致，不发送不共同支持的 temperature。
- 请求只允许一个 max_tokens，必须为正整数且 ≤16384（三个候选公共输出范围）；具体上限未选定，不把夹具4096或提案8192当成正式值。
- 同题同条件所有实际消息逐字一致；有 RAG 只能在末条 user 后追加该题冻结的 context 文件，禁止模型专属检索。原规格、TB、参考、top、检查数跨臂跨模型相同。
- 每题两臂、模型、样本编号严格平衡，新数据集前缀和独立账本。原槽拒绝重发。此版拒绝额外 assets，避免学校包静默丢失向量文件。
- 基类原放行哈希门控继续有效，并新增接入四个源码哈希、费用上限和各槽保守费用界绑定。无 release、DRAFT/夹具、已预约、UNKNOWN、STOP、费用缺失或超界均阻止下一槽。机会数界与费用界必须一起审核；这里不声称任意人工填入的费用界已经数学证明。
- 原始 usage、cost、响应模型/provider 完整保留。响应返回快照别名而非请求 ID 时会严格停止，不能自动认作同模型继续；公开目录不足以核实实际返回行为。
- 原执行器提取/本机异常仍使用 EXTRACTION_OR_LOCAL_ERROR 组合状态，原输出及错误类型照存。本次没有宣称已经解决该原执行器分类粒度问题。

## 正式统一流程（本次未执行）

1. 先选择下述 RAG 和模型/预算，审核20题来源与校准；另建正式数据集目录，冻结资料库、算法、每题实际context、原题/TB/参考、完整request和来源哈希。生成独立槽位ID，不复用旧336。正式 manifest 必须符合 console-frozen-v1 加 earlier-model-rag-v1 扩展。
2. 总控对完整材料审核，用户确认后才形成独立 release，绑定所有旧模块和新接入模块、manifest、transport、机会数、输出上限及费用界。本轮没有制作任何真实放行文件。数据清单里的 READY_FOR_REVIEW 也不等于放行。
3. 控制台“导入冻结包”→“选择放行文件”→选下一槽→“检查放行（不联网）”。确认真实执行时隐藏输入密钥→“运行所选一个槽”。每次仅一次POST，原固定测试和Yosys复用原通路。也可“导出隐藏Key终端入口”，生成绑定manifest/release哈希的单槽PowerShell脚本；它使用 getpass，密钥不进入脚本、argv或学校包。
4. 生成后保存原输出/RTL/请求/响应/usage/cost及本机阶段结果。不是PASS也保存；服务错误、身份不符、未知或基础设施故障按停止规则处理，403不再探针，不补样、不扩批。
5. 如需学校复核，选已有RTL槽，进入“学校”页，选一个工具，点击“打包一个案例”。VCS/Xcelium使用原TB/参考；DC/Genus必须各自选择与本题匹配的已审库/角/SDC。不得把旧组合题25的约束套给新时序题。
6. 打包产生原学校文件及单个 `console-…-home.zip`、本机 `…-home-record.json`。共享目录仅传ZIP。先点击“复制仅检查共享命令”：固定ZIP SHA核验、安全成员检查、复制至学校 `$HOME/xzy01-console-staged/<key>` 并检查全部字节，**0工具启动**。再在学校检查工具/库/许可证/约束准备情况；本次HOME校验不把缺依赖自动判成READY。
7. 准备齐全且获单例执行授权后，点击“校验共享文件并复制命令”，到学校终端人工执行。该新版命令先再次验证固定ZIP和HOME字节，再从HOME启动一个原run-one.sh。工作结果另存 `$HOME/xzy01-console-single/<key>`。已存在工作目录拒绝重跑。VCS/Xcelium/DC/Genus分别打包、分别手动执行，没有四工具循环或批调度。
8. 完成后平铺 `return-console-….zip` 与同名 `.json` 到共享根目录。失败保留HOME；只补传用“复制仅补传命令（不重跑EDA）”。同名异内容不覆盖。共享目录缺失或不可读就停下，不退回共享目录直接运行。没有实施Git、SSH或远程批处理。
9. Windows控制台载入对应 `…-home-record.json`，点击“回收结果并验hash”，选平铺sidecar；校验ZIP哈希后复用既有白名单、CRC、输入哈希、来源绑定和工具凭据导入。不得把 verified=true 当功能PASS。
10. “导出当前结果报告”生成独立配对JSON：机会分母、有效RTL数、各状态、both-pass/both-nonpass/help/harm/不可配对及每模型RAG差值。此表为描述性统计；题目相关性、置信区间及主分析须在正式包中另行冻结，不将重复样本当独立题。

学校说明尽量一次列齐，但本轮没有创建真实新模型学校单例包：尚无本批模型RTL，不能伪造。四工具生成和回收仅用夹具验证。

## 待用户选择及有限清单

**题目**：沿用 public-rag-all20-reconsider-v1/adoption.json 中20题，候选顺序不变；已看过，不宣称全新holdout。12历史重叠、2轮内相关、4契约问题原记录保留（类别来自先前排除，用户全部采用不抹去风险）。具体逐题source_bindings和标签见 draft-experiment.json；并非按新模型结果筛选。

**RAG选择项**（本次不选择、不生成新上下文、不改方法）：

- A：历史18片段BM25。依据是和既有真实实验的RAG处理相衔接；需对本20题按原规则生成并冻结新context，旧结果不能直接作为本批对照。该库历史选择过程与新轮独立设计要求的关系须审核。
- B：public-rag-independent-v1/A 的48片段TF-IDF。依据是该包先冻结通用资料与规则再读本轮候选，保留时间线；较符合本轮独立设计约束。仍需核定20题完整context及包装，不能据离线命中或成绩更换片段。
- C：public-rag-lexical-comparison-v1 已冻结的48片段 BM25Okapi/L/Plus 之一。它们是不同算法条件，不能在看过离线结果后称为盲选；若选需明确说明公开通用方法依据。为了隔离模型因素，当前不建议同时横向跑多种RAG。

推荐用户考虑 B，依据仅为先冻结后选题的设计顺序，**没有据命中/成绩选优，也没有实际采用或修改B**。embedding对照仍是后续独立方案。

**模型**：建议延续 4o-mini / 4.1-mini / 5.6-luna。更早/便宜不等于RTL更弱；同厂商也不消除训练、推理与服务差异。用户若改组合，新版本另行校验，不替换当前源码白名单或旧证据。

**机会与费用**：20×3×2条件×2样本=240，仍为待审，不增加到旧预算上。建议共同 max_tokens=8192 作为待选值（夹具用4096）；具体输入长度及token计费界未确定，max_cost_usd=null。上轮 $0.724 是假设平均token的示例，不是硬预算，不能据此开跑。各槽费用界必须结合最终提示、端点费率、输出含推理预算与可能附加费用，由审核绑定。缺cost时停止核账；不得把null记0或免费。

**固定检查数**：本轮不编译或仿真20题，只复用原资料。不以旧25的213或其他题检查数代填。每题需来源明确的已审固定检查数，契约冲突/相关标签及附加验证适用性纳入正式冻结前检查。

## 离线证据

- tests-initial.txt：初版12项通过，原样保留。
- tests-final.txt：14项通过。新模型导入，跨模型消息/推理设置拒错，超128KiB提示原字节交接，单次mock、403和UNKNOWN停机、未知费用停机、密钥不落盘、模型别名拒绝、功能失败不升级、四工具脚本生成、HOME真实解包、篡改拒绝、平铺导入及重复同内容幂等、配对统计检查。
- tests-regression.txt：原 test_lab/test_batch/test_dev/test_console_bridge 共46项，44通过、2跳过。包括原loopback测试（仅本机模拟服务），不访问OpenRouter。学校执行函数均mock，不启动商业工具。
- gui-offline.json：实际Tk界面导入6个新模型合成槽，无dispatch。
- preservation-before.json / preservation-after.json：对旧源码、模型提案、独立RAG/采用记录、历史执行/续跑及学校控制台证据的逐文件哈希核对。它是明确列举范围的检查，不声称覆盖全盘。

旧25槽四工具现场结论原样有效：VCS 0/212、Xcelium 0/211对冻结213均CHECK_COUNT_DIFFERENT；DC/Genus产物完整但有警告，当前网表没有自动门级验证。工具退出0、导入成功、固定测试PASS、门级验证、最终签核分开。未修改门槛。

材料留本目录供总控独立审核。本轮没有向其他对话发送消息，没有启动正式实验。正式冻结仍待上述明确选择与证据补齐，不能把离线接入完成称为240槽已获放行。
