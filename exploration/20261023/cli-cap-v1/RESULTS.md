# 已登录Codex的CLI能力核查（未生成）

客户端目录列出三个准确ID：gpt-5.6-luna、gpt-5.6-terra、gpt-5.6-sol，visibility=list、supported_in_api=true。这是目录元数据，不是三模型推理权限实测。登录状态依据总控最新login status及前轮原回执；本轮不读取auth文件、不提取token。官方文档说明model/list也可能返回内置/缓存目录，因此不以目录存在宣布调用成功。

本轮执行了3个非生成命令：本机codex-cli对应app-server generate-json-schema --experimental、exec --help、app-server --help，均exit0；schema生成使用新空CODEX_HOME，未复制认证材料、未使用用户第三方provider配置，未启动app-server/RPC、thread或turn。原客户端models_cache只提取白名单元数据。保存452个本机版本schema、原命令日志及SHA。

发现：
- exec支持--ignore-user-config，帮助说明保留CODEX_HOME认证；该选项没有出现在app-server帮助中，不能直接把exec选项套到server上。本轮没有启动带用户配置的server，也未请求HTTP中转。
- ThreadStartParams有baseInstructions、developerInstructions、config与allowProviderModelFallback；这些提供控制入口，但尚未验证能完全复现冻结的两角色消息。任何后续使用都必须禁用fallback，不能自动换模型。
- TurnStartParams没有直接completion输出硬cap或推理请求次数硬cap。对452个schema搜索max_output_tokens/maxCompletionTokens等形式为0命中；modelProvider/capabilities/read在该版本只给imageGeneration/webSearch。config允许任意键不是某个猜测键受支持的证据。
- 客户端truncation_policy=10000不是completion token上限。默认reasoning Sol为low、Terra/Luna为medium；没有擅自改成共同档位或改原省略设置。
- 一次CLI turn不能据现有材料证明恰好一次模型请求，也不能证明额外instructions与原system/user角色等价。离线prompt-input即使可渲染，也不能单独证明输出cap或实际请求次数。

结论：原协议的共同8192硬cap、单次推理和完整消息边界仍未建立，所以不启动正式生成。first-three-not-executed.json仅列三个模型各一个原冻结槽（原序号1/3/5），未预约、未发出、仍包含于原240上限；没有新题/替代模型/额外探针。实际生成0，usage和返回模型均未观测，不填假值。原API401是另一条认证失败证据，未重试，不能解释为CLI模型不可用。

只读schema扫描第一次使用系统默认GBK读UTF8失败；同源显式UTF8读取后完成，错误保留。没有重跑schema生成、参考校准或默认回归。原RAG/题目/所有封存包不改。

[官方app-server接口](https://learn.chatgpt.com/docs/app-server)；[缓存目录边界](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)；[开发命令](https://learn.chatgpt.com/docs/developer-commands)。
