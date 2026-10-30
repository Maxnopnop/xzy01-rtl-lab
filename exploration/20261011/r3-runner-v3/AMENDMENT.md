# 传输补验执行补记

首版transport-v1在首次新runner调用前因夹具提前创建call目录而触发WinError183；首个原argv短prompt已送达，新stdin尚未测试。首版脚本、输入/日志、失败说明和当时源码快照封存保留。修正测试另存transport_acceptance_v2.py/run transport-v2，配置改为在runner创建call目录后写入，未改变v2及历史材料。

v3准备门槛在正式传输验收前改指向新transport-v2；失败run的旧source-lock应与其source-snapshot核对，不声称它绑定当前v3 runner。transport-v2之后冻结的源码不再修改。

协议原“不重跑默认代理回归”收窄为“不覆盖原回归证据、不采用代理隔离隐去默认失败”。此次确有新runner/适配器代码，仓库AGENTS要求运行test_lab/test_batch/test_dev/test_fsm，因此在独立regression-v1保存一次原环境回归；不改全局代理，不删除失败，不循环重试失败测试。

总控复核补充：本批timeout/overflow均未派生后代进程。既有kill_tree被触发，负分支收据确认直接接收进程结束；后代进程树清理未在本批独立验收。REVIEW中的“超时树清理……通过”仅支持上述直接进程终止结论，不支持完整树清理实测结论。此次只追加run外限定，未改冻结源码/协议/证据，未新增测试或模型调用，24槽仍未启动。
