# 来源与边界

正式版：https://zhiyaoxie.com/files/TCAD25_RTLCoder.pdf
IEEE TCAD 44(4), April 2025, 1448–1461. DOI: 10.1109/TCAD.2024.3483089。
首页注明在线发表 2024-10-17，current version 2025-03-21。不与 arXiv 早期版混同。
补充仓库：https://github.com/hkust-zhiyao/RTL-Coder

核验 raw-prompts-20261016/README.txt 和 provenance.json：rt_sequence 是附加 Development-subset clarification 的 RTLLM 开发题；未改写归档原文为 rt_sequence.upstream.original.txt。sticky_alarm/event_parity/request_delay/debounce3 是项目自建开发题。system.txt 源自 rtl_lab.py。这些不是 RTLCoder 训练集，不能据此推断历史作者身份。

概念须分开：自动生成的指令-代码训练数据、公开评估题库、代码质量反馈微调、推理时修复。论文核心不是 RAG 或显式 IR。
本项目要求原题、提示词、参考资料在同一条件下跨模型一致，测试输入不变；论文方法不能直接变成项目实验授权。

全文读取所得供后续讲解核验：
- II.C–D pp.1453–1454：训练数据参考答案经语法检查，不保证功能正确。GPT-3.5 用于数据生成。
- III.B pp.1455–1456：生成多个候选，质量评分，再用比较损失和 MLE 联合训练；不是推理报错回传修复。
- IV.C p.1457：实际使用 Pyverilog；参考代码和语法通过的候选得 1 分，语法失败候选用 Rouge-L 与参考代码相似度评分。不能称为已实现功能奖励训练。
- IV.A pp.1456–1457：VerilogEval 与 RTLLM V1.1；后者 29 题，五次采样任一通过。前者每题 20 次，用 pass@k；试三种温度报告各模型最佳结果。不能直接当作本项目一次调用成功率。
- IV.B p.1457：删除 Rouge-L > 0.5 的约 100 条训练样本，是相似度去重而非严格证明无污染。
- IV.D p.1457：正文 EvalHuman/EvalMachine 与 61.2/41.6 的排列可能不一致；后续讲数值须核对 Table III 和 Fig.13，不直接照抄正文。
- V pp.1459–1460：功能验证及功能评分是未来工作。对 GPT-4 数据、模型规模的解释属于作者推测，不当作公开确认的架构事实。
