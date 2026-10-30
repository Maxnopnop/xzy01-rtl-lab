# 中断记录工程验收

独立stream_process.py/cli_adapter.py替代R5返回后才记录的方法；原版本不改。保存原stdout/stderr字节、每chunk时间/nonce/长度/hash，原prompt/SHA及request模型/命令/限制，PID+创建时间，原子fsync关键状态/退出proof。恢复逐项核请求、chunk覆盖/hash、退出流与单clean turn、usage/最终文件；只有完整返回可重建到新输出，缺失/部分一律UNKNOWN，不重发。

process-v1/v2分别13人工真子进程检查；后续静态复核发现请求context缺少最终文件边界及chunk恢复绑定，于新过程校验版本补齐，再process-v3做同13组，snapshot保留当前实际源。前两版通过只适用于当时较窄边界，不冒称覆盖后新增约束；原run未覆盖。三轮均无自然模型调用。v3之后6组recovery-boundaries验证错误exit nonce、错误chunk nonce、字节截断、必须最终文件但缺失拒收、补人工匹配文件后可重建、批离线重建保原bytes/48分母。批例2预约/1已知/1未知/46未启动，未调用模型。pipeline人工流测试v1/v2各48mock，v2对应最终分类/协议；格式失败首次仍进入F/R、role与judge.stage隔离、256KiB exact与over、两代码块/128KiB+1提取失败保留。模拟评分部分明确MOCK，不当成真实RTL功能证据。

v3中实际停止本任务拥有的写者进程，然后按该任务记录的子PID与创建身份核对并停止该子；桌面本体未关闭。活writer锁拒恢复，writer死但child活返回ACTIVE_CHILD，child死而无exit proof则UNKNOWN；即使已经出现completed但无exit proof也不重建。已保存exit proof但summary窗口写者退出，凭原证据离线重建，来源标明。陈旧锁原字节保留，recover不删除旧锁。全后代清理UNVERIFIED：只验证精确拥有的直接子进程，不声称树清理/生产恢复/桌面停止根因修复。

适配器版本/login预检只在实际生成函数执行时进行，auth probe raw不落盘；本次未运行真实CLI生成/预检，不改代理/模型/桌面配置。stderr为可信CLI诊断原字节，仍是本地受保护证据，不上传/提交Git；不保存密钥或机器auth文件。CLI自身内部连接行为不受本地逻辑预约数等同约束。

required-default-v1为唯一默认环境完整回归：34测试，3failure/1error/2skip，75.819s；两loopback方法未收到请求/RemoteDisconnected。原stdout/stderr/receipt与seal保留，未隔离代理重试到PASS。准备脚本曾有GBK默认解码UTF-8错误，纠正为显式UTF-8并记录；首次prepare又因控制summary无status发生KeyError，计划创建前停止，原源码与失败封存。gate改读取control-audit后准备成功。原工具返回的错误文本另存preparation-error-transcripts.txt，标明它是工具展示文本而非原生stderr字节。没有丢弃失败实验或重发外部服务。

资源snapshot：24逻辑CPU、约31.4GiB RAM（当时约14.7GiB空闲），离线Icarus串行；独立OS校准与纯Python控制曾最多2作业并行（校准写者+其子另计），模型拟串行。编译15s/模拟10s/人工进程≤6s，2GiB软内存预算无OS硬配额，750MiB磁盘阈值，准备时限10800s。未用满资源、不更改全局配置。账户只读snapshot普通用量允许/周窗口used4%，不是未来额度或可用性保证，未使用reset/credit/购买。

最后候选使用engineering-v2/runner.py与recover_batch.py，补充plan SHA/source/job/model/父阶段/exact prompt绑定；4新增人工检查均通过，原v1源和prepared-v1保留。恢复必须使用这个候选脚本，根recover_batch.py属于较窄旧工程版本，不作为生产恢复入口。
