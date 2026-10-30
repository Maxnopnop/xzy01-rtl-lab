# 有限执行器已实现，等待真实接入与总控技术核验

本轮完成core.py、http_once.py和dispatch.py：固定240槽/三模型/两条件/两样本，逐字发送原请求JSON；fsync预约在发送前，单一生产账本、并发排他锁、未知/403/服务异常即停、无重试。持久化原HTTP返回、usage、准确请求模型与返回模型、阶段、原测试回执。8192请求预算与返回usage检查、128KiB提取限、1MiB HTTP读取限保持。使用原冻结提取函数定义，不import生产runner。

完整返回与未知预约分开：回复已落盘但后处理失败/进程中断，记为完整返回待处理并停机；无完整返回的预约记未知，绝不重发。EXTRACTION_ERROR保留extraction阶段，多代码块不择优，编译/仿真不覆盖该错误。模型RTL才进入原测试/reference，旧参考校准不重跑。真生成、模型评分、离线mock和同源参考校准各自分开；全20不称合格holdout，原标签从旧包读取。

离线结果：第一轮27项中1个Windows长路径夹具错误，原stderr、receipt及修复前源码保留；缩短job目录后27/27通过；补齐中断清理与落盘后失败保护后29/29通过；另5项技术放行门槛检查通过。全部运输、网络、native进程均mock，0真实模型/HTTP生成/EDA调用。不是29个模型正确样本，也没有默认回归重跑。

新工具保护：每job8MiB、整run512MiB存储上限，超限停止，不扩预算。所有实际生成包括探针均占原240；首个未知/403不能补样。运行时配置/放行/账本位于runtime，不写入冻结源；预检记录副本initial-preflight.json冻结。

真实可行性：CLI登录状态沿用上轮只读证据，当前本机模型目录列出准确luna/terra/sol且supported_in_api=true；这不是本账户API权限。官方Chat Completions文档有max_completion_tokens契约；CLI共同输出硬cap未获正式接口证据，truncation_policy不能替代。代码不使用私有接口、不读取auth文件或提取登录token。当前runtime/route.local.json与API环境凭据未配置，technical-release也不存在，首次preflight按预期阻塞，0预约/0未知/240未启动。

剩余外部条件：真实API接入，以及总控对账户模型访问、预算契约、参数省略和可观测消息边界的技术审核。客户端发出的messages字节已离线验证一致；服务内部包装仍不可观察，不能夸称端到端已证相同。不再要求用户重批同一实验意图。最小字段和命令见SETUP.md。
