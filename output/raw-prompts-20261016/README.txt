这是一份原始题库提示词导出，不是模型调用结果，也不是已通过审核的RAG方案。
五个单题txt逐字符等于原manifest中spec字符串，UTF-8编码、不补写换行。manifest.original.json为整个题库manifest原字节副本（含未选入本轮的另两题）；五题选择单独列于provenance.json。
system.txt来自当前rtl_lab.py中的SYSTEM_PROMPT，与题目文本分开。ALL_PROMPTS.txt仅添加分隔标题便于阅读，不冒充实际发送消息。
rt_sequence.txt含历史Development-subset clarification，因此不是未经适配的RTLLM上游原题；rt_sequence.upstream.original.txt是上游归档原文，按manifest记录的SHA校验通过。其他四题为项目自建开发题。
本次未改任何题库、测试、探索准备材料，也未运行模型。RAG材料及完整请求尚未冻结，不在本包伪造。
