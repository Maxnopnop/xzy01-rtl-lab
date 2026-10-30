旧缓存client_version=0.163.0，当前npm=0.147.0；三模型均缺supports_parallel_tool_calls。原生bundled导出该字段均true，无转换；本轮两候选均无cache parse error。模型权限不由catalog证明。
候选1关闭更新/remote_plugin仍本地拒绝chatgpt/github；候选2显式参数与chatgpt_base_url使请求路径可见为/blocked-chatgpt/plugins/featured?platform=codex，github CONNECT仍被拒绝。两次停止。
原生bundle默认reasoning：Luna/Terra medium、Sol low；实际只捕获Luna，不推定未捕获模型实际请求。
