# 控制台 OpenRouter v1 交付验收

2026-10-24。仅本对话独立新增模块、入口、测试、说明；未改原GUI、冻结执行器、RAG方法、原题/输入/历史结果。未向其他对话发送消息。真实模型调用0，学校EDA调用0，自动化未恢复。

入口：仓库根 Open-Lab-v2.cmd；操作指南 CONSOLE_OPENROUTER_GUIDE.md。原Open-Lab.cmd保持可用。

|要求|结果|证据|
|---|---|---|
|OpenRouter固定endpoint、三个指定ID、不替换|源码支持＋mock通过|console_bridge/transport固定hash；tests-delivery.txt|
|Key隐藏、无磁盘/日志/argv/browser|mock落盘扫描与loopback auth通过；真人输入未验证|同上；console_cli.getpass、GUI密码框|
|完整实际messages一致、原请求字节传递|通过|同题同条件跨样本检查、单POST捕获；原文无重写|
|budget-policy|通过|calls_only无显式token上限；若冻结包明确输出上限则单独支持；不注入8192|
|未放行／跳序／重复／unknown拒绝|通过|后端gate、独占锁、持久预留、STOP；不是仅GUI提示|
|两臂三模型样本机会平衡|通过|同task sample列表、完整消息与输入SHA核验|
|生成后固定测试、Yosys分离|实际本机通过|real-local-slot025-v2/result.json：213检查0错误，SYNTH_PASS；输入字节相同|
|真实功能失败与基础设施失败分开|mock通过|功能失败保留；infra/timeout停止后续，不自动重试|
|新96＋旧240可列|通过，336槽|隐藏Tk测试、delivery-final/history-import.json|
|OpenRouter隐藏Key终端脚本|已生成、绑定hash及下一槽；离线通过|delivery-final/Start-OpenRouter-One.EXAMPLE.ps1为NOT_RELEASED示例|
|VCS/Xcelium/DC/Genus单例脚本|四种均已生成并离线核验|delivery-final/generated-script-matrix.json，12个bash -n通过|
|共享完整性／命令复制|文件哈希校验通过，GUI按钮源码支持|四工具生成与缺文件拒绝测试|
|失败回收／只补传|mock通过|人工ENVIRONMENT_ERROR回收；ship不增加execute次数，同包拒绝重跑|
|学校原输入绑定|通过|RTL与原模型响应重新提取字节比较；TB/ref与原冻结锁比较；请求/原预约/执行回执对应。替换任意三文件拒绝|
|不支持assets|明确拒绝|测试通过；没有静默省略|
|slot25商业计数|原样展示|211/212对213保持CHECK_COUNT_DIFFERENT，未改PASS|
|旧证据不变|6320个选定文件全部相同|delivery-final/preservation-after.json|

## 脚本与真实执行分层

|工具|新控制台离线|本轮真实执行|已有旧流程证据|
|---|---|---|---|
|OpenRouter|22项测试中的mock/loopback/终端导出|未调用|只读导入336槽，不当作新UI API验收|
|Icarus|适配与状态测试|已保存next96 slot25，213/0|原槽保留|
|Yosys|适配|WSL实际SYNTH_PASS|原96综合结果只读|
|VCS|脚本生成、语法/回收协议|未学校执行|slot25旧RTL/DC网表检查数不同，保留原状态|
|Xcelium|同上|未学校执行|同上，保留211/212等实际计数|
|DC|配置/SDC门槛、脚本/回收|未学校执行|slot25旧综合COMPLETED_REVIEW_REQUIRED|
|Genus|同上|未学校执行|本入口未把其他案例的Genus成功外推至slot25|

本版学校仿真使用模型原RTL，不自动拿DC/Genus返回网表进行门级重仿真。当前不宣称完整门级闭环、PPA/时序签核、独立oracle或服务隐藏包装等价。新学校脚本需要后续一次一例人工验收。

## 测试与错误保留

- 最终22/22通过，无跳过：tests-delivery.txt。
- AGENTS回归24项：22通过、2个原生Yosys测试Windows跳过；regression-default.txt。实际WSL综合另有单例证据。
- PowerShell解析2个入口无错误：powershell-syntax.json；学校Bash12个无错误：bash-syntax.txt。后者保留WSL主机代理提示，不是网络或模型调用。
- 早期失败保留：safe_id最初不接受模型版本点号；旧240的slots路径与原请求版本不同；本机stdout CRLF回执解析失败；学校mock全局改os.name导致pathlib错误；依赖门槛新增后历史测试fixture路径不完整。均在新增模块/测试修复，原数据不变。
- 一次apply_patch多次更新同文件被工具拒绝，已合并补丁；PowerShell rg字面通配路径及猜测run_synthesis.py路径读取失败，改用实际run.py。未因此执行外部操作。

delivery-final/为最终脚本矩阵/源码锁/样例与保持性记录；根下较早matrix/source-lock是过程证据，已被最终版本替代但保留。示例包没有正式放行，学校离线包用合成库路径与夹具SDC，仅供审核，不能用于学校运行。

验收尚需：用户双击v2的可见布局与真人按钮交互；未来新实验数据清单与总控正式放行；真实API服务及四工具新脚本的专项人工实测。本次实现与授权离线验收完成，到此停止，不扩功能或启动批次。

## 最终源码锁路径澄清
最终有效锁是 validation/console-openrouter-20261024-v1/delivery-final/delivery-source-lock.json。交付后再次逐项核验：9项全部匹配当前源码（0 mismatch），对应补修后22项PASS。上一层 delivery-source-lock.json 是补修前过程证据，4项与当前代码不同，保留但不得作为最终交付锁。两份锁均未覆写。
