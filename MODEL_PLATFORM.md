# 多模型 API 批量工作台

本工具是 Python 3.10+ 标准库脚本，不需要安装平台服务或 pip 包。复用已有固定任务、Icarus 仿真、调用预留和证据保存。当前只支持 Bearer 认证的 Chat Completions 协议；仅修改 base_url 不能接入任意厂商原生 API。本入口运行直接生成 RTL 的 baseline，尚未接入 FSM 状态表多阶段实验。

## 1. 建立配置表

在仓库目录用 PowerShell 执行：

```powershell
.\models.ps1 template
notepad config.local.models.csv
```

表格支持任意数量模型，也可用 Excel 打开并另存 UTF-8 CSV。列名、顺序必须保持如下；模板的示例行默认禁用，填写真实信息后改成 true。

```csv
id,enabled,protocol,base_url,model,api_key_env
vendor_a,true,chat_completions,https://api.example.com/v1,真实模型ID,VENDOR_A_API_KEY
vendor_b,true,chat_completions,https://api.example.org/v1,另一个模型ID,VENDOR_B_API_KEY
```

示例地址不能真实调用。base_url 填厂商文档的基础地址，脚本会追加 /chat/completions，不要填写完整请求地址。id 用英文、数字、下划线或短横线；不同模型可以共用 api_key_env。这里只填环境变量名称，不填密钥值；配置表默认被 Git 忽略。

## 2. 无调用预览

```powershell
.\models.ps1 check --tasks ve_count10 --samples 1
```

检查 CSV、地址格式、模型名、环境变量是否设置，显示计划调用数。该命令不联网，不能证明认证成功或模型存在。用 `--models vendor_a,vendor_b` 选择部分已启用模型。

## 3. 创建任务，再实际调用

先用两模型各一题一次，共两次上限。密钥可通过隐藏输入提供，只留在当前 Python 进程内，不保存到文件；prepare 与 run 分别运行时需要分别输入。

```powershell
.\models.ps1 prepare --run-dir runs\api-smoke-01 --tasks ve_count10 --samples 1 --max-total-calls 2 --prompt-keys
.\models.ps1 run --run-dir runs\api-smoke-01 --workers 1 --prompt-keys
Invoke-Item runs\api-smoke-01\platform-report.html
```

prepare 仅创建计划，零模型调用；run 才会消耗 API 额度。默认依次运行不同模型，每个模型并发 1，可显式提高 workers。Windows 若找不到 Icarus，可在 prepare 添加 `--iverilog D:\iverilog\bin\iverilog.exe --vvp D:\iverilog\bin\vvp.exe`。

也可事先通过本机安全方式设置所选环境变量，省略 --prompt-keys。不要把真实密钥写进命令历史、CSV、截图、聊天或 Git。脚本不会读取 .env 文件。

小试成功后，两个模型 × dev10 十题 × 每题三次：

```powershell
.\models.ps1 check --samples 3
.\models.ps1 prepare --run-dir runs\api-dev60-01 --samples 3 --max-total-calls 60 --prompt-keys
.\models.ps1 run --run-dir runs\api-dev60-01 --workers 2 --prompt-keys
.\models.ps1 report --run-dir runs\api-dev60-01
```

Linux/WSL 将 `.\models.ps1` 替换为 `python3 model_platform.py`，路径使用正斜杠。这个批量入口用于本机模型生成与 Icarus；学校 VDI 的 VCS/Xcelium 仍按既有单案例规则复核。

## 4. 预算、失败与复现

- 计划调用数必须不超过显式 max-total-calls，每个模型固定为任务数 × samples；不自动修复、补抽或跨模型回退。
- 可设置 max-output-tokens、api-timeout、temperature、token-field。默认不发送 temperature/seed；厂商不支持的参数不能假定有效。max-output-tokens 是输出上限，不是费用上限，输入及其他计费项目仍按厂商规则计费。
- run 重复执行会跳过已完成的 PASS、功能失败及 API 失败槽位。遇基础设施失败会停止后续模型；修复后显式再次运行可继续其他模型，已失败槽位不自动重试。
- INTERRUPTED 或存在未完成 attempt 的未知结果禁止自动重发。人工核对后如需重试，另建实验并记录额外预算。
- 配置在 prepare 时冻结；修改 CSV 不影响已建任务。改变参数或源码须新建 run-dir。多个模型顺序执行，不代表实验顺序已随机化。
- 汇总 platform-summary.json/csv、platform-report.html；每个模型目录保留标准 plan.json、summary.json、report.html 和逐样本请求/响应/RTL/仿真证据。请求及日志按已有机制隐藏密钥。
- 开发集成绩不是官方 benchmark 成绩；新的 API 结果不能直接混入旧 CLI pilot。Yosys 可在 WSL 对每个模型目录执行 `python3 synthesis.py --run-dir runs/api-dev60-01/vendor_a`，其综合结果单独保存。

尚未支持：原生 Messages/Responses 等不同协议、网页会话登录、按货币金额硬限额、任意自定义提示词、多阶段状态表方法。后续应新增专用适配器和版本化协议，不在配置表中保存任意请求头或密钥。
