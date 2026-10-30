# 单条件准备材料：已被统一 RAG 对照方案取代
2026-10-16。此目录是五个开发题族 × 三模型 × 两样本 = 30 槽位的中间准备记录，实际模型/EDA调用均0。后来用户追加 RAG / 无 RAG 两条件；唯一待审执行方案是同级 fixed-input-rag-v2 的60槽位，不是30+60。
保留原任务 manifest 中 spec 的完整字符串；系统格式来自既有 rtl_lab.SYSTEM_PROMPT。冻结原 TB、向量、参考，R1c 直接复制历史 testbench.sv/events.bin，包含原CRLF，不重建事件。R1b原参考和14/32步约束不变；新wrapper实例化原模块，DUT不改名，三文件read_verilog代替单合并文件，待静态复核及总控审核。
所有请求文件均为拟发送内容，没有实际发送证据。现有CLI不满足输出token硬上限及隐藏包装可观察性；本地API配置未发现有效的指定模型路由。此目录没有执行器或执行授权。
原prepare首轮CRLF比较失败保留在preparation-failures；修复仅区分语义行比较和原字节hash，旧输入没改。源文件和22,358项历史保全基线见source-lock.json/prior-bindings.json。
