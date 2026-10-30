# 控制台v3 recovery-r1 独立验收

结论：有限离线能力验收通过，可用于下一轮冻结包准备和离线导入；不构成真实模型或学校执行放行。

初版12源码/128证据锁正确，53/53测试通过，但HTTP错误和基础设施失败在result落盘至STOP落盘之间崩溃可放过下一槽。原失败证据见audit.json，原12源码保存在original-v3；未回写旧证据。

负责人有限修复后，总控独立核对r1的13源码/29证据锁，并在禁止外网和子进程的审计进程内复现63/63通过。总控另行重复两个原始崩溃探针，均在缺STOP时拒绝下一槽。修复包括持久结果schema/身份/RTL哈希/完整状态/基础设施标志核对及仅补传命令补齐share参数；不改变原题、RAG、prompt或评分。新增正常失败对照覆盖固定测试4状态与综合2状态，允许正常功能失败继续。

有效锁：../console-v3-recovery-r1-20261028/delivery-source-lock.json；bridge SHA256 492bb008b8d42c524a9241ea437ecb9b89f004cc9a1a08028687f69ec12816f5。总控独立结果r1/audit.json，原始日志r1/independent-tests.txt。源码/交付证据执行前后无变化。

限制：旧runner额外24项回归中，两个loopback测试受代理路径影响，产生3 failure/1 error，另2项native Yosys跳过；不宣称完整旧runner回归全通过。v3生成使用固定hash的独立transport.py，不调用旧api_worker.py，本次对该路径的loopback字节/单POST/禁止重定向已独立通过；不据此修旧runner或解除真实服务检查。真实账户推理与新版学校现场未验证，学校计数211/212对213继续CHECK_COUNT_DIFFERENT。

2026-10-28：通过后才向已有探索对话派发30候选准备，使用冻结48片段TF-IDF，20已有候选+最多10新增候选，先冻新增顺序，不按RAG命中选题；参考核查/风险分层/完整请求/控制台DRAFT_REVIEW包最终交用户审核。0模型，0执行release，0自动扩批。
