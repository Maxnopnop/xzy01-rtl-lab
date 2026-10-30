# CLI 完整构造捕获：有限负结果

固定npm二进制0.147.0及SHA；依据官方自定义provider文档创建新本地capture provider。预声明最多2路径，每路径至多3模型；实际只使用1路径、启动Luna一次即停止。无真实模型、无正式实验、无120次验证。未改原题/RAG/冻结源/全局设置，也未实现预算规则修订。

## 新获得的证据

127.0.0.1本地HTTP接收器捕获一份完整POST /v1/responses原始body和headers，然后返回故意的400 OFFLINE_CAPTURE_ONLY。没有上游转发或模型答案。CLI exit1按负结果保留。完整源码capture.py、命令、候选配置、计划、回执及二进制hash均可审查。

body含model、input、tool_choice、parallel_tool_calls、reasoning、store、stream、include、prompt_cache_key、text、client_metadata。input首先有developer additional_tools，再有developer消息与user消息；工具定义位于input内，不能仅查顶层tools。顶层没有instructions字段，冻结system/user逐文本核对结果见audit.json；不能仅凭字段缺失断言基础指令未发送。未进行字段删除或规范化，未计算虚构跨模型diff。

## 停止原因与隔离边界

只给子进程系统运行所需环境白名单、独立空认证HOME/CODEX_HOME；未读取复制auth。provider端点只指向loopback，无env_key、无需OpenAI认证；HTTP/HTTPS/ALL代理指向同一本地拒绝服务器，NO_PROXY仅localhost。不是OS防火墙级隔离，报告不声称全系统流量审计。

接收器观察到chatgpt.com:443及github.com:443 CONNECT请求并在本地拒绝，没有建立隧道。按计划遇外部尝试停止，Terra/Sol未启动。CLI另报模型缓存缺supports_parallel_tool_calls，不兼容；未修补缓存或重试。缓存来源曾用于prompt-input，但不能据此认定0.147 exec正确采用相同模型目录。该警告使默认模型能力/包装不可靠，所见Luna reasoning自动成为medium/context all_turns，尽管配置未指定reasoning。这不能归为正式模型默认差异结论。

因此本轮仅证明在该诊断构造下能抓到完整本地请求，并揭示prompt-input遗漏的字段；不能证明三模型完全相同，更不能把custom-provider responses-lite构造视为已登录ChatGPT内置通道发送等价。headers中responses-lite标记保留。技能、权限、环境和角色仍须按冻结协议单独审查，不能因共同附加就追认合规。

## 下一步最小接口要求

需要与固定二进制匹配且不触发外部发现的模型能力目录，以及已登录目标通道自身的完整离线请求导出/可审计构造接口，才能验证完整跨模型一致。仅修好mock缓存也不能跨越生产通道差异。若继续本地mock，须另审匹配目录来源、外部发现隔离与实际生产分支对应关系；本轮不擅自修补或另试。若无法取得该接口，应审查原始messages的API适配路线；不改冻结输入，不自动改预算、重试或模型。8192不是本轮停止原因。

既有锁核验见audit.json。工具编排最初一次提交在执行前发生SyntaxError，未运行shell/CLI，随后单独保存capture.py执行；保留此开发错误说明。真实模型0、正式实验0。

官方来源：https://learn.chatgpt.com/docs/config-file/config-advanced （custom providers）与 https://learn.chatgpt.com/docs/config-file/config-reference （base_url、requires_openai_auth、supports_websockets）。下一步待总控独立审核。
