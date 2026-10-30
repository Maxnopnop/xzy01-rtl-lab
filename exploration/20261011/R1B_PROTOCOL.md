# R1b 有限验证补强：执行前协议

2026-10-11。工作目录同本任务根，新增代码r1b.py，运行目录`runs/r1b-v1/`；冻结首轮四run、所有首轮脚本/协议/RESULTS。独立审计结果另存，不运行会改写首轮verification的audit.py。

## 校准与结束点

独立过程参考：rt_sequence用4bit历史寄存器；sticky_alarm用前一位与锁存；event_parity用异或累积；request_delay用独立阶段整数；debounce3用连续相反输入计数。均手写，不使用fixture_rtl生成，5参考先实际Icarus旧固定TB核对。参考与Python独立过程oracle同义，但还不是外部专家审核。

SAT校准至少：每题正确fixture/独立参考在14步无反例（5）；代表rt_sequence重命名语义等价实现14步无反例（1）；E4同一延迟故障12步无反例（1），14步有反例（1）；真实损坏Verilog语法（1）应SYNTAX_ERROR。共9次Yosys SAT命令调用，其中语法错误应在前端停止。校准通过才进入历史模型批。追加状态解析小测试涵盖TIMEOUT、UNSUPPORTED、ENV_ERROR、非零工具退出、无法识别输出，不当作真实工具验证。

预处理read_verilog -sv、hierarchy、proc、flatten、opt、async2sync、opt。set-init-zero，rst_n只在step1低，后续高。每SAT步是抽象clock tick，状态输出对应前一步输入；12位前缀位step2..13，失配step14。NO_COUNTEREXAMPLE_WITHIN_BOUND只表示有限界限/初始化/复位约束下无反例，不表示无界等价或任意异步释放正确。同步/异步复位、中途reset、任意初值、CDC/Mealy/多时钟不在已支持证明范围。

## 历史样本选择（新增SAT结果产生前冻结）

候选仅evidence/fsm48、paired-a32、paired-b64逐项已保存真实RTL，任务限定上述5题且原状态PASS/FUNCTION_FAIL。先按路径排序纳入所有原FUNCTION_FAIL（预计≤7）；再按task/model分层，每层路径最早的PASS各1；其余PASS按task/model轮转、路径顺序补到24。不同hash优先以减少同字节重复，但同一模型/任务/状态的原记录仍可保留并报告重复；上限24、列表/原result与DUT哈希/原诊断绑定。候选ve_fsm因本版本无独立过程参考不纳入，计排除范围。只依赖原成绩和元数据选择，不读取新增SAT结果，不修RTL、不改变旧标签。

每份在14与32步分别验证，最多48次Yosys。工具不支持的结构、语法错误、timeout、环境失败单列。模型RTL先通过既有extract_rtl限制校验，原字节复制，允许仅将声明模块名映射为gate，映射前后hash均保存。未知输出不算无反例。每个SAT反例解码rst_n/din，按step2..bound-1作为输入序列生成独立oracle见证TB并实际Icarus重放；若只初值或reset模型失配导致不能重放，标COUNTEREXAMPLE_NOT_REPRODUCED，不宣称新增真实错误。原PASS中出现可重放反例才算新增评分信息；原FAIL只证明已知错误可再发现。

资源：CPU顺序1，Yosys30s/次，Icarus compile15s/sim10s，总墙钟15min，目录预算100MB。完整批次≤57次Yosys命令、5参考Icarus+每反例1次Icarus。3连续环境/超时错误停止相关批；源码/旧证据锁改变停止。无硬内存隔离，受限单模块RTL，无GPU。所有未知/未完成保留。0新模型调用，0新增token；旧失败费用仍UNKNOWN。

403只做一次非调用诊断：已有CLI login status、本地CSV是否启用、Codex配置键名及模型/供应商/代理是否配置（不显示值中的密钥或代理URI）、旧四次错误证据。禁止再次刷新模型列表/exec或更改VPN、账户、系统路由；无已核验其他端点就记录阻塞结束。本轮不新建chat/监控或向其他chat发消息。
