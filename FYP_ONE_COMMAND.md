# FYP 原工具链：本机一键处理，学校单案例运行

范围：模型 API → RTL → Icarus → Yosys → VCS/Xcelium → 报告。ELEC5550 课程包、DC、PrimeTime、Innovus 暂不使用。本机已提供自动脚本；学校商业仿真仍需登录后人工选择一个案例。没有 SSH、SLURM、远程后台代理或全案例商业仿真循环。

## 完整工具清单

现在也可双击项目里的 **Open-Lab.cmd** 打开本机按钮窗口，无需输入命令。窗口使用 Python 自带的 Tkinter，不需要浏览器或额外服务器。当前本机 Python 已验证可用；其他电脑需要安装带 Tkinter 的 Python 3.10+。

1. **模型配置**：填 id、base_url、model、api_key_env，点击“添加 / 更新为启用”，再保存；下方也支持批量 CSV。用隐藏输入框填写 API 密钥，仅存当前进程内存。
2. **提示词与运行**：点击“粘贴完整提示词”或导入 UTF-8 文件。Windows 直接读取 Unicode 剪贴板，原始 CR/LF、首尾空白保存在独立字节缓冲区，预览只读。只有显示会将 CRLF 渲染成换行，发送和保存使用原始字节。
3. 选择“仅生成”或“仿真＋综合＋学校打包”。后者必须选与提示词匹配的固定任务；原有 dev10 提示词是单独的第三种模式，不会偷偷覆盖输入原文。设置重复次数与总调用上限，可先点击预算预览。
4. 点击“开始运行（消耗 API 额度）”后创建新实验，窗口下方显示日志。当前任务结束前不关闭窗口，不自动重试。新实验目录自动命名为 runs/gui-时间-随机ID。
5. **结果与学校传输**：按钮可检查工具、更新/打开报告、打开本次原始结果、复制学校命令、收取结果、发布 Git 包和备份。学校仍需人工登录并选择一个案例。

窗口关闭后密钥需要重新输入；提示词只在点击开始时保存到本机忽略目录。Git 操作使用本机已有认证；认证未配置时先按本文 Git 章节处理。

| 工具 | 用途 | 位置与权限 |
|---|---|---|
| Windows PowerShell | 统一入口 lab.ps1、models.ps1 | 本机已有 |
| Python 3.10+ | API、任务、报告、打包、校验 | 本机；只用标准库，无额外 pip 包 |
| 文本编辑器 | 编辑模型 CSV，粘贴完整提示词 | 本机 Notepad；不需要 Excel |
| 模型 API 与对应 API Key | 获取生成结果 | 厂商账号与额度；学校 EDA 许可不提供模型额度 |
| Icarus Verilog：iverilog、vvp | 编译和执行独立测试台 | 本机；当前 D:/iverilog/bin |
| WSL2 Ubuntu、Python、Yosys | 对原始 RTL 做通用综合检查 | 本机；当前已有；也可使用原生 Yosys |
| Git | 版本管理；可选学校包/结果传输 | 本机，Git 路线时学校也需要 |
| 私有 GitHub 仓库 | 保存脚本、冻结输入包；接收单次结果分支 | HTTPS 认证；不上传 API Key、账号日志、课程库 |
| Omnissa Horizon Client | 访问 vdi.ece.ust.hk / ECE LAB7 | 本机客户端，学校账号与 DUO；校外按学校要求使用 VPN |
| Horizon 共享文件夹 | 本机和学校传输 | 已配置 C:/Users/A/Documents/FYP，学校通过 ~/tsclient 访问 |
| Python 3.6+、Bash、tcsh | 学校菜单、环境加载与回传 | 学校 Linux；.cshrc 在 tcsh 中加载 |
| Synopsys VCS | 商业 RTL 仿真 | 学校安装与许可证；学校主机实际可用性由运行结果确认 |
| Cadence Xcelium | 第二种商业 RTL 仿真 | 同上 |
| 普通浏览器 | 打开本机 HTML 报告 | 无云端部署要求 |
| GitHub Actions | 开源工具离线回归 | 可选；不会运行学校商业工具 |

VCS 配置为 `/usr/eelocal/synopsys/vcs-vx2025.06-sp1/.cshrc`；Xcelium 配置为 `/usr/eelocal/cadence/xcelium2303hf/.cshrc`。流程自动加载。Yosys 只做 `synth -noabc` 通用综合，不代表工艺映射、PPA 或芯片签核。

## 先配置一次模型

在仓库目录打开 PowerShell。若本机已有 config.local.models.csv，直接编辑，不要再次创建。

```powershell
.\models.ps1 template
notepad config.local.models.csv
.\models.ps1 check --tasks ve_count10
.\lab.ps1 doctor
```

CSV 列固定为 `id,enabled,protocol,base_url,model,api_key_env`。填写真实地址/模型名，将 enabled 改为 true；协议当前为 chat_completions。api_key_env 只填写环境变量名称。`--prompt-keys` 在终端隐藏输入密钥，只保存在当前进程中，不写配置表。详细参数见 MODEL_PLATFORM.md。

## 粘贴完整提示词：原文模式

打开空白提示词文件：

```powershell
.\lab.ps1 prompt --task ve_count10
```

记事本打开 `config.local.prompts/ve_count10.txt`，把完整提示词直接粘贴进去，保存为 UTF-8。工具不在文件中放任何提示模板。处理过程使用 read_bytes/decode，不 trim、不转换换行、不添加系统消息、前后缀、任务规格或反馈。每次实际请求只有 `messages=[{"role":"user","content":原文}]`。

原文件字节和 SHA-256 保存到新实验，发送请求单独保存。这里的“原文”指你保存到 UTF-8 文件里的内容；如果编辑器自己改了换行，那发生在保存之前，可直接导入已有 UTF-8 文件避免编辑器转换。检测到提示词包含当前 API 密钥时拒绝发送，而非悄悄替换文本。模型服务自身的内部指令不在本脚本控制范围内。

原文要自动仿真，需选择与内容匹配的已固定任务 ID。脚本不修改提示词来强迫它匹配测试台：模块/端口/行为不符会如实失败。示例为两个已启用模型、每个一次，共两次预算：

```powershell
.\lab.ps1 local --run-dir runs\exact-count10-01 --tasks ve_count10 --samples 1 --max-total-calls 2 --prompt-dir config.local.prompts --prompt-keys
```

原文模式目前串行运行（workers=1），自动执行生成、Icarus、Yosys、两工具打包和报告。重复相同命令只处理未完成槽位；未知中断结果会停止，要求检查后另建实验，不静默重发。不要用旧 models.ps1/batch.py 入口继续原文实验。

输入任意设计但还没有对应测试台时，使用“仅生成”：

```powershell
.\lab.ps1 prompt
.\lab.ps1 generate --prompt-file config.local.prompts\full_prompt.txt --run-dir runs\free-prompt-01 --max-total-calls 2 --prompt-keys
```

这会把同一原文发送到所有启用模型，保存原始响应，标记 GENERATED_UNVERIFIED，不会捏造功能分数。该入口使用新目录，不自动重试；后续要仿真，需要为该设计建立并审核独立测试台。

## 使用原有 dev10 固定提示词

不提供 --prompt-dir 时，明确使用原有 baseline：通用约束＋任务规格。两个模型 × 十题 × 三次，最多60次：

```powershell
.\lab.ps1 local --run-dir runs\api-dev60-02 --samples 3 --max-total-calls 60 --workers 2 --prompt-keys
```

这个命令会消耗 API 额度；请先把调用数缩到一题一遍验证账号与模型。每个模型的请求独立，模型顺序执行。默认先确认 Yosys 可用，Windows 自动用 WSL Ubuntu，避免模型已调用完才发现综合工具缺失。若明确暂不综合，传 `--synthesis none`；报告显示未执行。

输出上限不等于金额上限；厂商对输入、推理等计费不同。本流程保证调用预留上限、不自动修复、不自动补抽。已有失败保留在分母内。新 API 实验与旧 CLI pilot 分开记录。

## 学校操作最少的方式：共享文件夹（推荐）

已有10个历史包、356个案例×工具选择已放在 `C:/Users/A/Documents/FYP/ECE-Transfer`，可以立即使用，不需要先调用新模型。

1. 登录 Horizon 的 ECE LAB7，打开终端。
2. 粘贴以下一行，按菜单选择一个实验/工具，再选择一个案例。

```bash
bash -c 'find "$HOME/tsclient" -maxdepth 6 -type f -name ece_menu.sh -exec bash {} \; -quit'
```

脚本自动复制到学校家目录、校验输入、加载 VCS 或 Xcelium、运行一次、收集源码/日志/退出码/版本、回传共享 inbox。无需手动填写 attempt、打包或复制 ZIP。它只执行一个案例，不能把356项自动循环运行。

3. 本机收取并打开报告：

```powershell
.\lab.ps1 collect
Invoke-Item workflow\lab-report.html
```

学校退出码为0不等于功能正确；本机核对完整执行、哈希、nonce、检查数与错误数后才记为 PASS。失败/超时也会回传，未返回为 NOT_RUN。此前一例真实 VCS/Xcelium 均通过，不会替尚未运行的新包填入通过成绩。

共享目录断开时，学校会保留 outbox 并打印 ship 命令。重试 ship 只复制文件，不启动仿真。

## GitHub 路线：无需共享文件夹

已将相同的冻结 ZIP 和 portable catalog 放进私有仓库 ece_git_packages；不是商业软件安装包。首次在学校执行：

```bash
bash -c 'git clone --depth 1 https://github.com/Maxnopnop/xzy01-rtl-lab.git "$HOME/xzy01-rtl-lab" && bash "$HOME/xzy01-rtl-lab/ece_git.sh"'
```

私有仓库需要认证，用户名为 Maxnopnop。HTTPS 密码提示应输入 GitHub token，不是网页登录密码；若用 fine-grained token，将权限限定到 xzy01-rtl-lab 的 Contents 读写，以便回传结果。不要将 token 拼进 URL、脚本或聊天。参见 [GitHub 官方认证说明](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)。未配置凭据管理时，clone 和 push 可能分别提示认证。

以后使用同一行更新并运行：

```bash
bash -c 'cd "$HOME/xzy01-rtl-lab" && git pull --ff-only && bash ece_git.sh'
```

菜单仍只运行一个案例。结果自动上传至 `ece-results/<唯一ID>`，不切换当前分支、不修改主分支或用户暂存区。传输失败保存在 `.ece-git-state`；只补传：

```bash
bash "$HOME/xzy01-rtl-lab/ece_git.sh" push
```

本机导入 Git 结果（也同时收取共享目录）：

```powershell
.\lab.ps1 collect --git
```

只 fetch 指定结果分支，不执行其中代码；按原始包、返回ZIP及内容进行验证。新克隆可从 Git 中冻结包恢复导入所需元数据，商业结果在 workflow/report.html 查看。Git 不保存完整未整理 API 账户日志；原始本机实验继续靠本地备份保存。

新增本机实验完成后发布新学校包：

```powershell
.\lab.ps1 export-git --push
```

或给 local 命令追加 `--publish-git`。发布仅提交 ece_git_packages 的变动，要求当前分支 main，不自动合并远端冲突。Git 方案已做本地裸仓库往返测试；学校 Git、网络与认证尚需首次实际运行验证，遇网络问题可用共享目录方案。

## 已有实验、备份和文件入口

已有实验无需重新生成，直接导出/更新菜单：

```powershell
.\lab.ps1 stage --run-dir runs\pilot60\model_01
.\lab.ps1 report
.\lab.ps1 backup --output validation\fyp-evidence-20261009.zip
```

备份命令收录本机 runs 和 workflow，可能含账户诊断信息，保存在本机私有位置，不上传 Git。输出文件必须新建，不能放入被备份目录。该备份不包含 API Key 配置或软件安装，需要自行保留环境配置方式。

| 入口 | 作用 |
|---|---|
| lab.ps1 / lab_flow.py | 统一生成、验证、打包、导入、报告、备份 |
| models.ps1 / model_platform.py | CSV 模型配置与默认提示词实验 |
| exact_prompts.py | 完整提示词原文发送与证据保留 |
| ece_menu.sh / ece_station.py | 学校共享目录菜单 |
| ece_git.sh / ece_git.py | Git 输入包与独立结果分支 |
| ece_desktop.py | 单案例商业运行、收集、补传 |
| workflow/lab-report.html | 本机 Icarus/Yosys 与已导入商业结果总览 |
| workflow/report.html | 每个学校包、案例和尝试的详细状态 |

本流程不自动关机。登录、DUO、Git认证以及学校每次案例选择仍由用户完成；本机 API 密钥和正式调用预算由用户配置。本机工具测试不能替代真实模型认证或学校商业工具验收。
