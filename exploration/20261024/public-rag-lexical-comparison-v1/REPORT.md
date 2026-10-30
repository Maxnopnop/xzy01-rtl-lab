# 离线检索组件比较（已完成；后续工作暂缓）

20个固定查询、同一48段资料、4方法，各一次，共80次。0生成/embedding/EDA调用。公开rank_bm25固定commit47aa3ddf8dc1ebeb7ef4e65f2b4536af44594099，Apache-2.0；原代码与许可证保留upstream。TF-IDF为本地基线。完整框架DeepV/VeriRAG/RTLRepoCoder因模型依赖未运行，不冒称复现。

|方法|涉及不同片段数|平均附加上下文字节|无命中|
|---|---:|---:|---:|
|TF-IDF|9|6355.90|0|
|BM25Okapi|15|6575.35|0|
|BM25L|13|6572.60|0|
|BM25Plus|13|6571.70|0|

TF-IDF/Okapi首选相同9/20、前三集合相同4/20；BM25L/Plus首选相同20/20、前三集合相同18/20。变化不等于质量提升；片段多样性、无命中率不能替代相关性或RTL正确性。没有独立qrels、没有RTL调用，不能选出优胜者。单次CPU时间仅观察值，不是稳定速度基准。

使用统一词分割、shared-token资格过滤、完整分数降序/ID平分及top3。共同过滤是实验包装，不是库原生完整RAG；BM25L/Plus会给不含查询词的文档非零基线分，不能用分数>0定义相关。参数均为上游构造默认，不针对题目调整。

results/generic-check.json的14项通用fixture通过。results/audit.json核验80唯一组合完成、输入锁不变、旧142项封包哈希不变。results/retrieval保留所有48段排名、选择片段和完整附加context；results/summary.json为汇总。离线runner禁用网络socket和子进程入口，这是应用层措施，不宣称OS防火墙证明。

用户随后将优先级切到已有RAG/noRAG实验结果一致的解释。本次不再新增算法、embedding、模型运行或基于结果调参。Embedding横向方案见相邻rag-equal-results-diagnosis-v1/embedding-comparison-proposal.json。

公开方案来源：
- https://github.com/dorianbrown/rank_bm25
- https://arxiv.org/html/2510.05327v1
- https://github.com/HArt-Git/VeriRAG
- https://arxiv.org/html/2504.08862v1
