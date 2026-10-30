# 显式Astrill代理：完整36新批次离线交付

待总控独立审核；本交付未创建真实release、未调用模型。新36为用户明确要求重新开始的独立批，不是接续旧35、不删除占用、不补写旧成绩。累计预算：旧1 UNKNOWN + 旧脚本1 HTTP403 + 新36 = 最多38次机会，未发送的旧槽不计调用。

## 输入与变化

055/124/072三题、openai/gpt-4o-mini / openai/gpt-4.1-mini / openai/gpt-5.6-luna、no_rag/rag各2样本。新ID rag36p1-001..036，slot-mapping.json逐一映射原槽、上次脚本槽和原request SHA。36请求逐字节复用；原spec/TB/ref、48段RAG、检索、完整messages和参数不改。输入目录含原归档资料用于保全，执行只由batch.json的36新ID决定；300草案仍不放行。

唯一实际传输变化：proxy_url=http://127.0.0.1:3213，proxy_env=None。OpenRouter HTTPS endpoint、provider.only=[openai]、fallback=false、各模型参数保持不变。route-config.json同时绑定source-lock-r1与release；verify用已审transport.route_values解析并与batch.route核对。send_once只走配置代理，CONNECT openrouter.ai:443，再发送原request bytes。代理失败/403不会切换直连、其他代理或模型。没有修改系统配置、注册表，没有安装LSP/TUN。

本机代理可达不等于模型地区限制已解除。此任务未做真实网络/付费探针，也不能承诺403恢复；若再次收到403，保留并停止。旧403为完整错误回执，原complete_http_return=false字段指未取得HTTP_OK，不意味着403正文不完整；原字段不改。

## 继承的执行保护

复用上一批已审r2短路径脚本机制，reuse/transport.py原字节SHA7ba1d3b47e2e471a9f11d226c65700d3cd70535b581fe7863a4fa4ed27c98524。本批source-lock-r1、route、batch、父证据锁均独立；不改公共GUI、旧runner、旧release或旧账本。gate仅接受NEW36_PROXY_SCRIPT_EXECUTION_RELEASE，必须同时批准旧UNKNOWN/403保留、显式3213及禁止直连fallback。原GUI release和上一脚本release均拒绝。

Start-Experiments.ps1默认Status；Run先离线预检，再一次隐藏key输入，顺序最多36，不每槽确认。密钥仅进程内存，finally恢复或移除环境值。短根live/jobs/001..036，发送前756路径实际写读检查，主响应文件在预约/POST前打开。新批单进程锁、RUN_STARTED持久记录、全局跨入口预约及本地预约在POST前写入并fsync。未知/中断/崩溃后禁止自动重启，不能删预约或STOP。旧父锁逐槽核对，旧两批后续槽若产生预约也阻断。

正常FUNCTION_FAIL/COMPILE_ERROR/SYNTH_FAIL保留可继续；CHECK_COUNT_DIFFERENT、服务/地区/身份错误、UNKNOWN、超时、工具或提取错误停止。原始响应与usage/cost留存；主保存失败尽力另存fallback证据后停，磁盘完全失效仍以预约防重。禁止重试、补样、扩批、换模型或后台启动。

## 离线验证

offline-audit-r1.json共28项：继承24项完整36、功能/编译失败继续、检查数差异停止、长路径、独占锁、防重、真实os._exit崩溃、保存失败、源码篡改等，再增加代理CONNECT五状态单POST、代理拒绝无直连fallback、环境代理不继承、route改变拒绝。所有模型回执为本地注入；代理网络连接类为mock，socket.connect被拦截。不是模型成绩或真实服务可用性证明。

powershell-audit.json检验实际PS5.1入口以假可执行文件模拟preflight/run，一次隐藏输入且清理环境key。复用的真实bridge.local_replay通过mock进程断言快照导入、三阶段命令及结果路径；未重跑原参考、未执行真实EDA。Python/Icarus/Yosys工具存在及二进制hash只读核对，非全OS/动态库可复现保证。

父证据锁保留前两事故、两份旧release、请求与全局预约；874份原冻结包不变。上一批首轮测试失败仍在原目录，本批不倒改。旧代理回归失败、同源参考非独立oracle、Luna medium非等计算量、学校211/212对213限制全部保留。费用无token/美元硬上限，两次旧usage/cost未知，不能按零费用或新费用和解释完整账单。

## CMD模板

当前只读状态（不联网）：

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch\exploration\20261029\main36-proxy-newbatch-v1\Start-Experiments.ps1" -Action Status
```

正式启动模板（总控出具新release后填入其真实绝对路径，模板不可直接运行）：

```text
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\Codex\2026-09-25\xzy01-using-llm-for-digital-chip-2\outputs\rtl-batch\exploration\20261029\main36-proxy-newbatch-v1\Start-Experiments.ps1" -Action Run -Release "<总控新代理批次release绝对路径>"
```

仅用户手动执行；代理须由用户保持运行。不安排自动化，不自动启动学校工具。完整回执结束后另做结果审计。
