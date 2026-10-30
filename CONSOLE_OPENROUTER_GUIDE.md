# XZY01 控制台 v2：OpenRouter、历史结果和学校单例

入口：双击 **Open-Lab-v2.cmd**。原 Open-Lab.cmd / lab_gui.py 保持原样；v2 内也有“打开旧控制台”。无需安装新依赖，使用带 Tkinter 的 Python 3.10+。

## 先查看已有结果（不需要 Key）

1. 打开 v2，默认读取 **新96＋旧240＝336槽**。可切换“读取新96”“读取旧240”。读取不调用 API，也不重新跑工具。
2. 选择一行，详情显示实际消息内容的 SHA-256、实际完整请求文件路径/hash、原始状态、usage/cost、模型请求和返回标识。缺失字段保持 null，不估计费用。实际消息 SHA 使用确定性的 JSON 编码比较 role/content/顺序；网络发送仍使用原请求文件字节，不重新序列化。
3. `status`、`fixed_test`、`synthesis` 分开。新生成的 `GENERATED_UNVERIFIED` 只表示取得 RTL；功能结论看 `local.fixed_test`。旧240的 `REFERENCE_PASS/FAIL` 是旧协议原始参考评分，不能包装成规格完全正确。
4. 新96已有 Yosys结果会显示；旧240此入口未绑定综合证据时显示 NOT_VERIFIED。学校页显示 slot25 的已有 DC/商业仿真结果：211/212 对原213明确为 **CHECK_COUNT_DIFFERENT**，不能升级为 PASS。
5. “所选 RTL 本机复验＋Yosys”在本对话所属的新目录复制字节完全相同的 RTL/TB/reference，真实执行 Icarus 和 WSL Ubuntu Yosys。不会覆盖旧结果，不人工修RTL。综合是通用 synth-noabc，不是 PPA、形式等价或时序签核。Windows需D:/iverilog/bin，WSL Ubuntu需yosys；任一工具缺失或超时记录失败。

## 导入新冻结实验与 OpenRouter

新实验仍由探索对话唯一准备；本控制台不选题、不检索、不修改RAG或提示词。当前 public-rag-independent-v1 的方法和冻结执行器均未修改。

1. 导入探索按下述格式提供的 `console-package.json`（数据清单，无可执行脚本入口），再选择总控审核放行文件。导入、消息SHA核验、查看预算都不联网。
2. 固定模型为 `openai/gpt-5.6-luna`、`openai/gpt-5.6-terra`、`openai/gpt-5.6-sol`；同题同条件各模型/样本的完整system/user消息一致；两臂样本编号和数量平衡；原规格/测试/参考/资产哈希一致。
3. 预算服从清单 `budget_policy`。`calls_only` 表示**无显式token硬上限，按冻结调用数，记录实际usage**，不注入8192或其他上限；`calls_and_output_cap`仅用于明确审核了输出上限的包。同调用机会不等于实际token/费用相等。
4. 点击“检查放行（不联网）”。后端必须确认该槽是冻结顺序中的下一个未预约槽、放行内容及完整桥接源码hash匹配、无历史/本控制台重复槽、无STOP或未知预留。
5. 只有未来明确获准执行时，才在隐藏框输入Key，点击“运行所选一个槽”。每次一个POST，固定 `https://openrouter.ai/api/v1/chat/completions`、OpenAI provider、无fallback/重试/重定向。Key只在当前进程内存，或读取进程环境中的OPENROUTER_API_KEY；不写脚本、磁盘、日志、命令行或浏览器。窗口关闭清空输入；代码不承诺Python字符串内存物理擦除。
6. 调用前独占锁＋永久预约。同槽完成、失败、UNKNOWN均不能重发；批次基础设施失败/超时停止后续。真实功能失败保留并按冻结顺序继续，不补样。生成后自动接本机固定测试和Yosys，状态分开保存。输出提取失败及服务异常保留并停止，不自动纠错。

### 是否自动生成脚本

| 入口 | 实际产生／使用的脚本 | 自动执行范围 |
|---|---|---|
| OpenRouter GUI | console_bridge.py复用已审transport.send_once | 仅明确点击后发送下一个已放行槽 |
| OpenRouter终端 | “导出隐藏Key终端入口”生成PS1，调用console_cli.py run-next | 用户启动后再次核验hash、顺序和放行，再输入RUN和隐藏Key；不循环 |
| VCS | run.csh、run.tcl、console_school_runner.py | 学校用户手动启动一个案例 |
| Xcelium | run.csh、run.tcl、console_school_runner.py | 同上 |
| DC / Genus | synthesis.tcl、launch.csh、已有ece_synth_school.py及公共校验模块 | 使用用户已审SDC和对应工具库路径；不猜约束或库 |
| 四工具共同 | run-one.sh、check-share.sh、ship-only.sh、console-manifest.json | 分别为运行一个、只检查共享、只补传；补传不重跑EDA |

所有学校包都是独立目录，清单绑定逐文件hash；回传ZIP仅含白名单。**Key、许可证、标准单元库字节不进入包。** 库路径和指纹可以记录。学校依然需要用户登录VPN/Horizon后手动逐个执行，不支持SSH或批处理。

本版学校仿真输入是保存的模型RTL；**尚未自动读取DC/Genus返回网表并串联门级重仿真**。已有slot25门级结果仅只读展示。导出前将RTL重新与原模型响应提取结果比较，将TB/reference与原冻结输入锁比较，并核对请求/预约/执行回执；含附加assets的槽明确拒绝学校导出，不能静默省略。

## 学校操作

1. 实验页选一个已有RTL槽；学校页选VCS/Xcelium/DC/Genus，再“打包一个案例”，选择已映射到学校的共享目录。DC/Genus额外要求选择对应工具配置JSON和当前槽的已审核SDC。不要把别的设计SDC视为已审核。
2. “校验共享文件并复制命令”先核对本机共享目录全部文件hash，再复制一条学校命令。只有用户在学校终端粘贴才执行。学校侧还会再次校验清单和输入。固定HOME案例目录防止同包重跑。
3. 共享目录不可见：先用“复制仅检查共享命令”，核对Horizon映射；此命令不跑EDA。执行已完成但复制失败：恢复映射后用“复制仅补传命令”。不要再次运行run-one.sh。
4. “回收结果并验hash”：选择本地打包记录（重开窗口时需要），再选择共享包目录 `inbox/<key>/console-return.json`。校验ZIP哈希/CRC/白名单、原输入及清单、来源/nonce、日志回执。重复导入同ZIP只读已有记录。失败也回收日志；无法信任的输入漂移拒绝计为有效结果。
5. 新四工具桥接脚本**尚未在学校实跑**。已有slot25学校结果来自原流程：DC综合COMPLETED_REVIEW_REQUIRED、Xcelium/VCS固定检查数不同。不能拿旧结果当新脚本的学校验收。

## 探索负责人：数据导入格式

`console-package.json` schema=`console-frozen-v1`，字段：

```json
{
  "schema": "console-frozen-v1",
  "name": "唯一新批名称",
  "budget_policy": "calls_only",
  "max_calls": 6,
  "proxy_url": null,
  "files": {"spec.txt": "SHA256", "tb.sv": "SHA256", "ref.sv": "SHA256", "request001.json": "SHA256"},
  "slots": [{"id": "唯一批次前缀-槽ID", "ordinal": 1, "sample": 1, "task": "原任务ID", "condition": "no_rag", "model": "openai/gpt-5.6-luna", "request": "request001.json", "spec": "spec.txt", "testbench": "tb.sv", "reference": "ref.sv", "top": "TopModule", "expected_checks": 213, "assets": []}]
}
```

这是字段示意，不是完整可执行包；必须包含同题两臂×三模型平衡槽位，ordinal从1连续。所有请求、原输入、参考资料/冻结方法文件均列入files；请求必须已包含固定provider字段，不由GUI增补。assets可用于本机附加文件；本版学校单例入口仅适配现有VerilogEval三文件任务，其他协议应另版本适配并审核。

总控另行提供放行文件，decision=`CONSOLE_EXECUTION_RELEASE`，user_approved=true，owner=`exploration`，reviewer_thread_id为总控ID；绑定manifest_sha256、bridge_sha256、transport_sha256、`console_bridge.bridge_bindings()`返回的source_hashes、max_calls、budget_policy、完整有序permitted_slots、automatic_retries=0、request_timeout_seconds=180。

本机放行文件是项目审核流程记录，不是密码学签名；同权限用户可编辑文件，因此需要总控实际审核，不能自行伪造“已审核”。UI没有生成正式放行文件的按钮。本次只生成了 **NOT_RELEASED 离线示例**，没有新批执行授权。

## 2026-10-24 验收范围

- 源码：独立新增bridge/UI/CLI/学校适配模块；旧Open-Lab入口、lab_flow、模型执行器及RAG方法不改。复用模块通过console_dependencies.json固定hash；已审transport SHA也硬绑定。
- 离线：22项测试，含真实loopback单POST/auth/重定向拒绝，mock消息字节、Key不落盘、额度、跳序、重复/未知拒绝、两臂平衡、原证据保持、学校四工具脚本生成、失败回收/只补传、hash篡改拒绝、导出前原输入绑定及不支持assets拒绝。最终通过数见tests-delivery.txt。mock不是模型或商业EDA成功。
- 本机：保存的next96 slot25原RTL及原TB/reference在独立目录实际Icarus **213/0**、WSL Yosys **SYNTH_PASS**；源文件字节保持。首轮CRLF回执解析失败保留，修复只在新增桥接解析层，不改TB/结果/检查数。
- 回归：AGENTS要求的test_lab/test_batch/test_dev共24项，22通过、2因Windows缺原生Yosys跳过；本次另有实际WSL综合单例。
- GUI：隐藏Tk窗口实际创建、336行读取、选择详情及密钥遮蔽测试通过。v2可见布局、双击启动和真人全流程点击尚需用户验收。
- 未验证：v2真实OpenRouter服务调用、新学校四工具脚本的真实执行、服务隐藏包装与真实后端snapshot。没有新模型或学校调用，不恢复自动化。

证据全部在 `validation/console-openrouter-20261024-v1/`：tests-delivery.txt、regression-default.txt、real-local-slot025-v2/result.json。最终源码锁、336行读取摘要、四工具脚本矩阵及历史保持核验在delivery-final/；先前生成的脚本矩阵保留为开发过程证据，以delivery-final为准。离线示例生成的四工具包使用synthetic库路径与夹具SDC，**仅供代码审核，不能用于学校执行**。

本轮首先双击Open-Lab-v2.cmd，确认出现336槽。后续每次一个用户操作，真实模型执行必须等待探索包及审核放行。
