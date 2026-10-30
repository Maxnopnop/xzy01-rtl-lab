# R2收尾工程修复（事后记录，不改变实验设计）

冻结r2.py真实执行完成20次生成、20项judge和summary，dispatch为GENERATION_COMPLETE。随后写evidence-lock时在Windows持有batch.lock(run)的一字节锁期间读取run.lock，PermissionError导致命令exit1。原源码、协议、模型输出、判据、summary均保留。不是API失败，不重复任何模型调用或仿真。

新增r2_finalize.py仅在原进程退出、锁释放后核验20项已完成产物，并第一次封存evidence-lock.json；其后r2_analyze.py只读核验哈希、CLI事件、固定judge资产和60份Icarus收据，输出放在run外。此为事后工程收尾，不是新实验臂、择样或统计分析变更。
