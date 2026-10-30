# 最小真实接入配置与启动步骤

执行器代码已完成；此文件不要求再次批准20题测试意图。当前缺真实API接入和总控技术放行，不能把ChatGPT登录token当API密钥。

1. 在本目录runtime/route.local.json放置route.example.json的两个字段：endpoint（默认 https://api.openai.com/v1/chat/completions）和api_key_env（默认OPENAI_API_KEY）。不要填model别名或改变请求参数，三个准确ID已固定在240请求中。
2. 在以后启动执行器的同一个PowerShell窗口，以本机安全输入设置该环境变量。密钥只进环境，不写JSON/聊天/命令行参数，不从Codex登录文件提取。示例：

```powershell
$ragApiSecret = Read-Host 'OpenAI API key' -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new('', $ragApiSecret).Password
```

不自动购买、充值或创建账户。若已有API接入，提供非敏感endpoint和环境变量名即可；真实密钥只在本机设置。环境变量只对同一窗口及其子进程生效。

3. 总控用正式公开模型元数据接口核对本账户三个ID的访问，再核对官方输出cap契约、准确HTTP messages、返回model ID规则及参数省略语义。任何收费生成探针都必须作为本批一个已预约槽位，不能单独试跑；403或未知立即停、不重试。当前没有执行任何认证HTTP元数据或生成请求。
4. 总控在runtime/technical-release.json签入技术审核记录，依据technical-release.example.json绑定当前batch/source lock/route hash并列出证据。模板本身是NOT_RELEASED，mock门槛夹具不是实际放行，不能复制成生产审核。
5. 执行下列命令。preflight不发HTTP或生成请求；run只在审核和配置全通过后才按固定顺序执行，且始终使用同一runtime/live-run账本。

```powershell
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B './dispatch.py' preflight
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B './dispatch.py' run
```

从本执行器目录运行。run每次发请求前写入并fsync预约，所有实际尝试累计最多240。未知预约、残留exclusive.lock或STOP.json不得删除后重新起批。崩溃时保留原目录，先只读核对；已完整保存的HTTP返回可以记为待后处理的完整返回，但不会重发或自动继续。没有自动解除停机命令。

默认不走已登录CLI：本机目录确有三个ID且supported_in_api=true，但默认reasoning等级不同；truncation_policy的10000不是输出cap。正式配置参考和当前help尚未证实共同8192硬cap和两角色实际消息，不猜配置键、不改成其他模型。

[官方Chat Completions输出上限](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)包括可见与推理token。[官方配置参考](https://learn.chatgpt.com/docs/config-file/config-reference)和[公开模型列表接口](https://developers.openai.com/api/reference/resources/models/methods/list)是本次核查来源。API文档不等于本账户已获权限；没有声称已观察到服务内部包装。
