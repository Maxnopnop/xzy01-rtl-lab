# 初步发现
已有96槽位配对修复研究不是端到端评测；公开v2在163个开发单处故障上100%，复合故障未验证。本轮选此缺口，避免重复历史验证。
外部检索2026-10-10：AutoFSM https://arxiv.org/abs/2512.11398；LLM-FSM https://arxiv.org/abs/2602.07032；VeriRefine https://arxiv.org/abs/2607.18519。结构化IR/分阶段检查已有近邻工作，不能单凭这些机制主张新颖性。
完整FSM测试方法具有前提约束，后续需与W/Wp等比较：https://isa-afp.org/entries/FSM_Tests.html 和 https://www.site.uottawa.ca/~bochmann/Curriculum/Pub/1991%20-%20Test%20selection%20based%20on%20finite%20state%20models.pdf 。本轮不宣称实现W方法。
双字段修改结果：序列检测1209（原漏160）、报警164、奇偶36、延迟应答501、去抖1209（原漏16），新版全部检出。扩大到同状态空间三字段修改；还需要明确有限公开轨迹对扩展状态实现的限制。

高阶总44048，非等价44046，等价2；新版0漏检，原漏982。扩展状态5/5可通过公开例子但实际RTL失败。研究边界是实现状态空间而不仅是修改处数。独立审计全部PASS，详情REPORT.txt。
