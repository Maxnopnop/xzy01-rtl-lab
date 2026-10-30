# v3 recovery-r1：仅恢复判定与补传提示修复

2026-10-28，待总控独立复核；不构成真实实验放行。本轮0模型生成/embedding、0学校工具，没有进行外部资料查询。未改题目/RAG/prompt、探索目录、真实release或运行账本。

修复范围：仓库根 console_bridge_v3.py、console_school_runner_v3.py。test_console_multimodel.py 仅将成功mock local结果补齐真实执行器已有的 infrastructure_stop=false；新增 test_console_recovery_r1.py。

## 恢复规则

原缺陷成立：result.json已保存但STOP.json尚未保存时进程死亡，后续gate只看result存在，误允许下一槽。r1 gate对所有已预约目录逐一读取持久结果，完全不依赖STOP是否成功落盘，不会在恢复时写账本或重试。

结果新增schema=console-result-v3-recovery-r1。允许继续必须同时满足：当前schema、GENERATED_UNVERIFIED、请求hash与冻结slot一致、请求/返回模型和provider一致、保存RTL hash一致、local为对象且 infrastructure_stop **严格为布尔false**，固定测试属于 FIXED_TEST_PASS/FUNCTION_FAIL/COMPILE_ERROR/CHECK_COUNT_DIFFERENT，综合属于 SYNTH_PASS/SYNTH_FAIL。

HTTP/重定向/身份/协议/unknown/提取错误，以及任意基础设施故障均拒绝后续槽；缺文件、损坏JSON、未知schema、关键字段缺失/类型错误、不认识的状态也拒绝。普通合法功能失败、编译失败、综合失败仍可继续，且已运行槽始终不能重发。

此策略保守拒绝旧v3无schema结果，**不自动迁移**。本修复未改变任何已有结果。旧v2仍用原入口；当前尚无正式运行v3批次，未来真实包仍需总控以r1源码重新绑定审核。

## 仅补传命令

学校传输失败提示现包含必需share参数，脚本路径和share都用shlex.quote转义，形式为：

`python3 '<HOME包目录>/console_school_runner_v3.py' ship '<共享根目录>'`

新增集成测试使用含空格和单引号的共享路径，模拟一次执行与传输失败，解析打印命令后进入ship分支，成功补传且execute调用次数仍为1；未调用实际EDA。

## 验收与绑定

- tests.json / tests.txt：**63/63通过**，包括原53项与新增10项；进程审计钩子禁止外部网络和子进程，仅loopback HTTP允许，无触发事件。
- 新增7种STOP写入前死亡：HTTP_ERROR、UNKNOWN、重定向、基础设施、身份、协议、提取失败；每例仅1mock POST，STOP不存在，gate及dispatch下一槽/重发均拒绝。
- 缺损结果测试覆盖删除、损坏JSON、非对象、空对象、关键字段缺失、未知schema/status、local异常类型、0/字符串false/true冒充安全标志；均拒绝。
- 正常对照覆盖4种固定测试状态×2种综合状态的8组合，全部允许下一槽；随后实际mock发送第二槽成功。
- runner-regression.txt：首次test_lab/test_batch/test_dev回归有3 failure/1 error/2 skip，两个loopback HTTP测试未收到请求、报RemoteDisconnected。urllib检测到系统http/https代理（未记录代理值）；仅测试进程设置NO_PROXY=*的复验另存runner-regression-no-proxy.txt。检查确认旧rtl_lab.clean_env白名单不传NO_PROXY，故该隔离手段不能传入API worker，两个loopback测试仍失败。保留失败日志，不修改此次范围外的旧runner或系统代理；不能宣称完整runner回归通过。学校工具未启动。
- delivery-source-lock.json：r1独立完整源码清单，相对仓库根；source/保存这些字节的完整副本。release-source-hashes.json：运行放行必须使用的精确bridge_bindings；仍未创建release。
- preservation.json：旧128项交付证据、总控original-v3内12份原源码、159项v2/学校与6320项历史证据校验；旧锁原文件不覆盖。
- evidence-lock.json：本revision自身证据锁，相对本目录。

旧20261024源码锁仍描述修复前版本，不能用于当前根目录r1代码。原12源码完整保存在validation/console-v3-independent-review-20261028-v1/original-v3；本目录before/额外保留3个修改前文件。新锁替代当前源码绑定，不改写旧交付历史。

本轮有限修复到此为止；总控复核前不得放行真实调用。
