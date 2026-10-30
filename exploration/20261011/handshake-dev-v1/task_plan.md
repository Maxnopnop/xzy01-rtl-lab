# 独立开发：握手事务判据 v1（0模型）

1. 预声明事务/背压/复位/有界终止契约与验收矩阵：in_progress。
2. 独立checker、手推trace及手写小RTL；不取R7源码/测试/波形作为开发golden：pending。
3. 有限离线校准：合法延迟/无效载荷通过，loss/duplicate/order/backpressure及空转拒收检出；原失败不覆盖：pending。
4. 默认required回归一次、保留失败/skip/全部原stdout，不改代理/隔离重试：pending。
5. 历史/R7封存保全及新包封存、提交总控后停止：pending。

资源界：最多24手推trace fixture、10手写RTL配置；Icarus顺序1，compile15s/sim10s；unit60s/default回归180s，准备总墙钟3600s/磁盘250MiB/软内存2GiB（无硬隔离）。只测试本任务RTL，0学校/模型/403请求/候选检索。修复只新版本/新run，原run/错误保留。

## 当前关闭状态

1–3完成：独立文字契约/collector/checker/22trace及10native配置全部符合预声明，source/run锁封存。4默认required3module执行一次24tests、3failure1error2skip，exit1，完整失败原样保留不重试。5历史20065/R7原封存只读核验通过，报告/新包封存后即提交总控并停止；不释放模型或集成生产判据。
