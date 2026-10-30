# OpenRouter配置与只读预检

此目录默认不含真实route或technical-release；示例provider_only为空会阻止正式调用。用户不需要在聊天中贴API key。

1. 在用户自己的PowerShell运行总控提供的 `validation/openrouter-setup-v1/Setup-OpenRouter.ps1`。该脚本安全输入密钥，只做key/models元数据检查，结束恢复进程环境。它的成功不代表推理权限。最新总控回执check-20261023T113443188105Z.json已确认key认证与三精确模型目录可见，生成0；仍需上游端点审核。
2. 总控核对精确目录ID `openai/gpt-5.6-luna`、`openai/gpt-5.6-terra`、`openai/gpt-5.6-sol`，并核对各模型上游端点目录，再填写共同唯一provider slug与响应中的provider名称；不能猜测、自动替换或改用其他模型。`provider.only`底层可能匹配多个端点变体，需审查具体slug。当前没有这项证据。
3. 本地复制 `route.example.json` 到新建 `runtime/route.local.json`；使用OpenWeb时可从 `route.openweb.example.json` 开始，其显式代理是 `http://127.0.0.1:3213`。只在用户确认本机该代理可用时选此项。route只存HTTPS endpoint、env名、无凭据代理URL或proxy_env名、经审查的provider信息，不存key。proxy_url与proxy_env只能选一；都null明确直连，不自动读取Windows/HTTP_PROXY。
4. 可在本机同一PowerShell会话安全设置进程环境并执行以下只读预检（不会联网、不会生成或创建放行）：

```powershell
$taskSecret = Read-Host 'OpenRouter API key' -AsSecureString
try {
    $env:OPENROUTER_API_KEY = [System.Net.NetworkCredential]::new('', $taskSecret).Password
    & 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B 'E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261023/direct-api-v1/dispatcher.py' preflight
} finally {
    Remove-Item Env:OPENROUTER_API_KEY -ErrorAction SilentlyContinue
    $taskSecret.Dispose()
}
```

此示例适用于尚未设置该进程变量的专用终端；若已有变量，用总控提供的保存/恢复方式避免清除已有配置。不要把key写到命令参数、route、聊天、截图或版本库。预检只输出credential_present布尔值。一个终端的env不会自动进入另一个已运行的Codex进程；未来执行必须在有该变量的进程启动，代理由route显式传给worker。

本版本支持直接HTTPS和无凭据HTTP CONNECT代理；HTTPS代理URL/SOCKS/带嵌入账号的代理会拒绝，不能默默降级。TLS使用系统/Python默认受信任证书验证，不关闭验证。

## 正式执行边界

只有总控独立签入绑定source/input/route及元数据证据的technical-release后，运行入口才接受run。首段建议permitted_ordinals=[1,2,3]，计入原240机会。不得把technical-release.example.json改个decision后冒充审核；它缺具体绑定且默认全部未放行。

当模型权限未知时，不做额外推理探针；总控放行后，在正式槽逐次观察HTTP与精确返回model/provider，失败或UNKNOWN停止，不补样。不购买，不自动充值。模型目录可见与key认证不是推理/账单权限证明。
