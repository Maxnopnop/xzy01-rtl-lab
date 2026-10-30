# 控制台使用与首次验收（2026-10-15）

本记录由控制台专用对话维护，不替代总控计划。代码检查及本机离线执行；0 真实模型调用、0 学校工具执行、0 上传。原始配置、历史结果、探索源码及根计划均未修改。证据目录 `validation/console-20261015`、夹具目录 `runs/console-validation-20261015-01` 均为本轮独立目录，Git 忽略它们，需保留在本机。

## 打开与初始检查

在本仓库双击 `Open-Lab.cmd`。它调用 `Open-Lab.ps1`，寻找 Python 3.10+ 和 tkinter，再启动 `lab_gui.py`。启动不请求 API。预计窗口标题为“XZY01 RTL Lab — 本机实验控制台”，四个页签，底部显示“就绪 · 打开窗口不会调用 API”。启动器路径来自源码；双击启动、窗口可见布局和真人点击尚未验收。

指导用户时一次只做一个步骤：首先仅双击入口并确认窗口是否出现。收到反馈后再指导进入第3页“结果与学校传输”，点击“检查本机工具”。这个检查不联网、不执行学校 EDA，也不等于 Yosys 综合链路通过。暂不点击“开始运行”或 Git 发布。

## 功能地图（源码支持，交互未逐项验收）

| 页面／按钮 | 真实调用链 | 副作用与边界 |
|---|---|---|
| 1 添加／更新模型 | add_model → csv_rows → model_platform.profiles | 改窗口文本；尚未保存 |
| 保存配置 | save_config → 临时 CSV 原子替换 | 写本机 config.local.models.csv |
| 填写密钥 | enter_keys → save_config → 隐藏输入框 | 先保存配置；密钥在窗口内存／子进程环境 |
| 检查配置 | check_config → save_config → model_platform.py check | 本地语法及预算检查，不验证远端账号或额度 |
| 2 粘贴／导入 | clipboard_text／read_bytes → OriginalPrompt → 只读预览 | 原始 UTF-8 字节缓冲与显示分开；真实剪贴板尚未本轮实测 |
| 查看预算 | preview → options → save_config → build_command | 不启动子进程，但会保存 CSV |
| 开始运行 | run → 新 run／原文文件 → lab_flow.py generate 或 local | 真实 API 消费入口；本轮禁止执行 |
| 仅生成 | lab_flow generate → exact_prompts | 无匹配固定判据，不能声称功能 PASS |
| 仿真＋综合＋打包 | lab_flow local → model_platform／exact_prompts → batch／Icarus → synthesis → 学校包 | 固定 dev10 任务须匹配提示词；并非任意 RTL 通用验证 |
| 3 检查本机工具 | lab_flow doctor | 只读发现工具；不保证后续路径、编译与综合成功 |
| 更新／打开汇总报告 | lab_flow report／open_path | 更新 workflow 报告；默认历史列表不等于扫描所有新 GUI run |
| 打开本次结果 | open_last | 仅当前窗口 last_run；重开窗口后不保留 |
| 共享目录／复制命令 | open_path／剪贴板 | 复制不执行；学校人工一次一个案例 |
| 收取共享结果 | lab_flow collect | 导入结果并更新本地状态，不能当只读预览 |
| 发布 Git 包 | lab_flow export-git --push | 导出、Git 暂存／提交／push；属于外部写入 |
| 收取 Git 和共享结果 | lab_flow collect --git | 网络获取及本地导入 |
| 项目／指南／备份 | open_path／lab_flow backup | 备份写所选 ZIP；未验证备份实际内容 |
| 4 保存／检查综合配置 | save_synthesis／ece_synthesis.py check | 写本机配置；不启动学校工具 |
| 选择 SDC／切换工具 | choose_sdc／switch_synthesis | 重新要求审核约束；不能把勾选当真实设计审查 |
| 刷新样本 | ece_synthesis.candidates | 回读已有原始 RTL 候选 |
| 生成单案例包 | ece_synthesis.py pack | 冻结一个样本与一个工具；不运行 DC/Genus |
| 查库／综合命令 | 复制到剪贴板 | 真正运行仍需学校人工操作 |
| 收取／综合报告／启动记录 | ece_synthesis collect／open_path | 回传绑定及人工审阅状态；不自动宣称功能或时序 PASS |

## 实际结果及证据

| 项目 | 状态 | 证据与限制 |
|---|---|---|
| 原始 GUI 单元测试 | 失败，3项中1项失败 | gui-tests.txt；已有本机库配置导致“应为空库”断言失败，非真实综合失败 |
| 隔离配置后同一 GUI 测试 | 实际执行通过，3/3，无跳过 | gui-tests-isolated.txt；创建隐藏 Tk 窗口，真实 doctor 子进程；生成调用、剪贴板和打包启动由 mock 替代 |
| 原文 UTF-8／CRLF／空白／禁止覆盖 | 实际执行通过 | 上述测试；非法 UTF-8 被拒绝。不是模型收到原文的端到端证据 |
| 配置拒绝重复 ID／密钥列、预算拒绝超限 | 实际执行通过 | 上述测试；合成配置，不读取或输出真实密钥 |
| 预算预览和错误处理 | 实际执行通过 | boundary-results.json；没有启动子进程，确认保存 CSV；预算0触发中文错误，弹框调用由 mock 捕获 |
| 离线 adder8 | 实际执行通过 | offline-init.txt、offline-run.txt、run 下 summary.json；65,536 次检查 PASS，real_generations=0，model_call_reservations=0 |
| WSL Yosys 自动选择 | 源码支持、探测通过，综合链路失败 | synthesis-mode.txt=wsl；verification.txt、synthesis-outcome.json：WSL path conversion failed，未启动综合 |
| WSL 路径诊断 | 实际执行通过 | wsl-path-diagnostic.json；反斜杠路径丢失分隔符，正斜杠转换返回0。没有据此宣称综合通过 |
| 单例与统一报告生成 | 实际执行通过 | run/report.html、validation/console-20261015/workflow/lab-report.html；单独 state，未更新真实 workflow |
| GUI 可见布局、双击启动、真人点击 | 未验证 | 隐藏 Tk 测试不能替代交互验收 |
| 真实 API／学校仿真／DC／Genus／Git传输 | 未验证 | 本轮未执行；历史记录不可冒充本轮通过 |

这些 PASS 均为开发夹具或边界测试，不能用于模型正确率。报告中 Yosys 的 NOT_REQUESTED 来自原离线结果；本次尝试失败的事实另存 synthesis-outcome.json，不能仅看报告判断完整流程。

## 改进优先级

1. **先修 WSL 路径传递**：lab_flow.synthesize 的 wslpath 参数在当前机器失去反斜杠。建议在隔离副本中测试正斜杠路径或 WSL 直接执行参数方式，并覆盖空格目录；验证一例真实 Yosys、来源哈希绑定和适当回归后再提出公共模块变更。当前 lab_flow.py SHA-256 为 `6e66c213c1dd3e3e41c3f634e124efb7ac52a02a59d147452f91422a70b2da58`。须先核对活跃实验源锁是否包含此文件，不能顺手修改。
2. **消除预算预览写配置的副作用**：让预览验证内存中的 CSV，显式保存或运行时再写盘；现在先在说明中明确副作用。需核对 lab_gui.py 的源锁归属再修改。
3. **测试配置隔离提前到窗口构造前**：原 test_lab_gui 在读取用户综合配置之后才 patch 路径，导致测试随机器配置变化。此次独立 verify_console.py 在构造之前隔离模型及综合配置，未改原测试或用户配置。
4. **改进结果入口**：历史与本轮结果应显式选择，避免“汇总报告”被误认为包含所有 GUI 新实验；后续需用独立 registry 重现遗漏范围再修。

未修改公共代码，未提交或推送。源码与结果哈希见 evidence-hashes.json。可复现脚本为 validation/console-20261015/verify_console.py；需先存在指定离线夹具 run。该脚本捕获已知综合失败并生成验收材料，退出0不能解释为综合通过。

## 后续学校验证授权与分工
用户准备打开 ECE 平台。控制台对话负责配置、按钮、单例打包、命令复制、回收与报告；实际 DC/Genus 执行及原始证据审阅由既有“FYP：实验与综合验证”对话负责。先确认用户当前界面与学校 ZIP 下载实际路径；不能假设已进入桌面或已下载。人工一次一个案例，DC 回收审阅后才 Genus；共用同一 RTL/SDC/工具与库指纹和结果来源链。不启动重复 EDA、不调用模型、不上传库或密钥、不恢复定时任务。上述授权不改变本轮验收的“学校未验证”结论。

## 2026-10-16 新主线控制台验收要求（待实现／待验证）
已阅读 AGENTS.md、FYP_FIXED_INPUT_RTL_RULES.md 与 validation/R1BC_RULE_REVIEW_20261016.md。以下为后续验收要求，不代表现有GUI已满足，也不构成执行放行。
- 冻结并在执行前后核对原规格、接口、输入、固定向量、测试台、参考、既有事件流及选择清单SHA256；不改输入语义。
- 同题三模型完整实际消息逐字一致，包含system/user、消息顺序与隐藏包装；不注入模型名或样本号，不能仅核对模板或预览hash。
- 原规格经一次LLM调用直接产生RTL；无先行计划/IR、候选IR、反馈、私有测试、人工修RTL或自动纠错重试。
- 保存准确请求ID gpt-5.6-luna、gpt-5.6-terra、gpt-5.6-sol；相同样本数、调用机会、输出预算和共同设置。实际token/cache/推理消耗及后端身份局限另列，不静默替换模型。
- 同一未修改RTL依次接受原固定测试、冻结R1b有界SAT及R1c事件/复位检查；同分母，失败/不支持/超时/未执行单列。反例另存，不回写原输入或提示词。
- 执行前冻结与总控审核为必要关卡；探索对话独占新批准备和执行。控制台不重复派发，建议30次上限不等于执行放行。
- 历史R1b/R1c保留但不能整体标成纯规格单次直接RTL基线。fyp自动化保持暂停，不扩批、补样、采购或启动学校任务。
本次仅更新控制台所属文档；未修改代码、模型配置、总控计划或实验源码。
