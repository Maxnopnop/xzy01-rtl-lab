# 新8题96槽：启动验收通过

2026-10-24，用户已批准“用这些题开始吧”。新执行器已技术放行，仅覆盖原冻结8题×3模型×2条件×2样本=96槽。正式生成仍为0，当前进程没有OpenRouter密钥，需用户在终端安全输入启动。

## 核验结果

- 独立核验8份生产源码锁、255输入锁条目、254文件原封包、2个工具哈希。32组三模型完整请求仅model不同；没有重新检索、修改RAG或改题。
- 8次原参考别名编译、8次原测试仿真均零差异，已对照实际命令、返回码、原始stdout、SHA和复制的原参考/test字节。这只是工具兼容校准，不是模型成绩或独立正确性证据。
- 本地HTTP模拟104次：96个成功槽位的捕获字节均等于冻结请求，8种服务/传输异常各1次。重新进入账本无新增发送，97槽被拒绝。31项mock检查、12项门禁检查通过。
- Windows PowerShell 5.1及当前PowerShell的密钥临时输入/环境恢复/预检失败阻断检查通过。实际release绑定下使用子进程合成key运行本地preflight，ready=true、network_requests=0；未创建live-run。
- 技术放行文件：探索新执行器 runtime/technical-release.json。原题包的“未启动”计划保持冻结；实际结果进入独立runtime/live-run账本，旧240槽不补跑。

## 新执行控制修复

1. 超128KiB模型文本、超1MiB HTTP响应、工具超时/原TB超时、磁盘限制均明确停止。
2. 已保存stop:true结果即使尚未写STOP，重启也补写STOP并禁止继续。已有未知预约不重发，已收到但未处理的结果保留为恢复状态并停机。
3. 空密钥变量不再视为已配置。

初次协调审核脚本的日志正则未处理Windows CRLF，读取阶段断言失败；修正为按splitlines解析后通过，没有重跑EDA或模型。探索保留校准时初版源码锁；之后只修订ledger/runner控制，core判题、工具、传输与输入保持一致，无额外校准执行。

## 执行范围

OpenRouter精确openai/gpt-5.6-luna、terra、sol，provider只允许openai，无fallback。并发1，单请求180秒，最多96个预约机会，无8192token硬cap或整批墙时硬cap。记录实际token、reasoning/cache及报告费用，缺失null。服务/协议/未知/资源/哈希错误停机，不自动重试、补样、继续或扩批；正常生成RTL的编译/功能失败保留为结果。原参考依赖与multi-hot覆盖缺口继续单列，无新增SAT、独立向量或学校操作。

## 用户终端命令

```powershell
& 'E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch\exploration\20261024\public-rag-next-executor-v1\Start-Experiments.ps1' -Action Run
```

密钥仅进程内使用，脚本结束恢复原环境。若停机，保留终端输出与新账本，不重复启动尝试补跑。所有前置审核已完成，不需要再次确认同一实验许可。
