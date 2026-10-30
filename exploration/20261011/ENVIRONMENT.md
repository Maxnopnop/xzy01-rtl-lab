# 本机环境与授权核实

日期2026-10-11（Asia/Shanghai），探测命令的host日志UTC可能显示10月10日，用户日期采用客户端时间。

- CPU Intel Core Ultra9 275HX：24核/24逻辑处理器；RAM总约31.4GiB、首测空闲18.8GiB；E盘首测约114GiB空闲。GPU RTX5060 Laptop，8151MiB VRAM，首测47℃、约1159MiB占用。结束快照见cpu.json、memory-end.json、gpu-end.txt、disk-end.json。没有采样峰值RAM/CPU功耗，不能声称硬配额或持续温度测量。
- 首测未发现python/iverilog/vvp/yosys/ollama/llama活动进程；Ubuntu WSL2原处Stopped，探测启动它。Windows Icarus复用现安装；版本和二进制hash记录在每run/environment.json。Yosys0.52在Ubuntu `/usr/bin/yosys`，内建SAT可用，E5实际运行。sby、z3、boolector、ollama未在WSL PATH。
- Windows PATH的python是商店占位符；真实Python复用`C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`。不安装依赖、不修改系统设置。
- 常用模型缓存`C:/Users/A/.ollama/models`、`C:/Users/A/.cache/huggingface/hub`和D:/models、E:/models未列出权重；11434/1234/8000/8080未见监听。本轮未全盘搜权重，结论为“未发现可直接使用的本地模型”，不能说机器绝无模型。
- 本地models CSV前两个条目均禁用且是example.com模板。没有向模板端点发送请求，不打印密钥环境变量。
- `codex login status`确认已有ChatGPT登录，CLI0.162.0。用户经总控授权本阶段研究预算暂无限，允许本机全部资源；仍冻结有限批次20调用、2并发。4次实际调用失败，模型列表HTTP403且workspace routing discovery失败。CLI内部WebSocket/HTTPS重连可见，不属于4次应用turn以外可量化的研究调用；不声称后台HTTP次数或零服务消耗。费用/token未知，0有效生成。没有换渠道、重置额度或绕过限制。
- 离线单并发是本批小FSM的资源选择而非永久低比例限制；约几秒至18秒就完成新增信息，不需要GPU或更多并发。未发现OOM/超时/磁盘问题。本轮没有学校工具执行、上传、关机、消息发送或新建其他聊天。
