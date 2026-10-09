# 架构与扩展约定

## 现有模块

`lab_gui.py` 是独立 Tk 本机窗口，通过子进程调用已验证的 `lab_flow.py` 和 `model_platform.py`，不修改运行器。Windows 完整提示词粘贴直接读取 Unicode 剪贴板；UTF-8 字节缓冲区是唯一发送来源，只读文本框仅作预览。后台任务通过队列更新 UI；密钥只进入子进程环境，配置 CSV 只保存变量名。`Open-Lab.cmd` / `Open-Lab.ps1` 提供双击启动。

`fsm_study.py` 是独立两阶段实验调度器：`codex_adapter.generate_text` 复用现有禁工具生成通道；`fsm_ir.py` 负责有限状态表数据解释，`fsm_checks.py` 明确区分公开反馈与私有判题。它输出兼容独立 Yosys replay 和学校单案例导出的任务结果。协议见 `FSM_STUDY.md`，不改变原 60 次 pilot 的统计口径。

```text
batch.py（计划、进程池、锁、续跑、调用上限、报告）
    ↓ 每个样本在独立 Python 子进程中运行
rtl_lab.evaluate（样本证据、生成、提取、固定输入检查）
    ├─ codex_adapter.py：已登录 Codex 直接生成
    ├─ api_worker.py：兼容 Chat Completions 的 HTTP 请求
    └─ backends.SimulationBackend
          └─ IcarusBackend：编译、仿真、统一结果
    └─ synthesis.py：可选 Yosys 通用综合，独立阶段结果

pilot.py：冻结两个/四个模型实验、轮次顺序、汇总及成对 task-cluster bootstrap
synthesis.py --run-dir：对已有 RTL 做单独综合，哈希绑定原始结果，不生成新 RTL

school_bridge.py
    已有样本 → 单案例 VCS/Xcelium 包 → VDI 手动运行 → 统一凭据导入
```

`tasks/` 保存评测输入，`examples/` 是工具链测试夹具，模型不获得这两类参考实现或测试数据。供应商访问层与仿真器相互独立，增加模型接口不需要改变判题器。

## 增加任务

1. 明确规格、模块接口、位宽、符号、复位、优先级、时序及未定义行为。
2. 编写独立参考模型/固定 testbench，添加正确和有代表性的错误 DUT。
3. 在 `tasks/manifest.json` 添加唯一 `id`、`module`、`spec`、精确 `checks`、`tb_sha256`；额外向量文件放在 `assets` 的相对文件名→SHA-256 映射。
4. TB 顶层为 `tb`，用 `!==` 检查 X/Z，最终只写一行 `RTL_LAB_V1 <nonce> checks=<n> errors=<n>` 到 `verdict.txt`。nonce 从 `+nonce=` 读取。
5. 运行正确和错误实现验证，再以新 run 进行模型实验。

`build_tasks.py` 固定随机种子；生成向量不使用当前模型输出。若改变已有题目定义，应创建新的任务版本与新实验，保留旧结果。

## 增加自动仿真后端

`backends.py` 定义 `SimulationBackend.evaluate(folder, spec, tools, args, secret) -> dict`。返回统一的 `status`、`stage`、`message`、阶段耗时和判题凭据；日志保存到样本目录。

新增后端需负责：工具发现/版本与许可证预检查、编译和执行参数、阶段超时、取消后的远端/本地进程清理、日志回收和统一判题。目前 CLI 有意仅开放 `icarus`；新增商业自动后端时同步扩展配置与 `inspect_tools`，不能仅换命令字符串。

`judge_simulation` 与模型供应商无关，可复用。不同仿真器不应共用编译产物；必须记录版本和 backend，结果单独汇总。

## 学校连接与专业工具的边界

目前**仅实现手动 transport**，不是自动商业 backend。`school_bridge.py` 的 VCS/Xcelium 命令模板与统一证据协议，为后续适配保留边界。

若学校以后允许远程自动化，新增例如 `transports/ssh.py`：上传不可变的案例包、提交单次运行、轮询状态、下载证据、取消进程。连接地址、账号和许可证设置保存在本机环境或不提交的配置中。不要将主机地址/凭据硬编码进任务或提示词。

若未来获得调度集群，队列/资源申请应属于 transport/scheduler 层；不能假设当前学校 SLURM 支持 EDA。认证成功与商业软件许可证可用是不同检查。

## 结果兼容性

- `plan.json` schema 2：计划任务、运行参数、源码和任务哈希。
- `result.json`：样本最终状态，尝试目录保留历史。
- `summary.json` schema 2：计划/完成/待完成、分类、真实生成次数、调用预留、token usage。
- `package.json` schema 1：商业工具回传需对照的原始来源哈希与 nonce。

综合已有独立 stage/result，不把仿真 PASS 当成综合或签核 PASS。后续形式验证、PPA 继续遵循同样边界。多文件/多模块设计需要版本化的文件清单和更强隔离，不宜直接取消现有单模块限制。

`batch.SUITES` 将原有 `custom` 与 `dev10` 分开，核心 runner 同时固定所选 manifest、源代码、来源锁和划分锁；任务目录属于配置，不硬编码在 evaluator 中。`build_dev.py` 从随库上游快照确定性生成开发集，不调用模型。整个 Yosys 工作进程在 WSL/Linux 内运行，复用 POSIX 进程组超时清理；Windows 模型生成与 WSL 综合以文件哈希交接。

## 固定 IR 的配对研究扩展

`paired_bank.py` 维护独立版本 `benchmarks/paired-v1`：规格、公开例子、私有输入、过程 oracle、状态图、错误表及开发/候选保留划分。`bank-lock.json` 固定全部数据字节，不能据运行结果修改既有 bank。

`paired_study.py` 每个配对复用同一张错误 IR、同一规格与模型；feedback 条件只增加公开契约的执行结果。一个分支一次新调用，每次调用启动前预留额度；结果不明的调用不重发、不退预算。A 阶段 32 次的可靠性检查通过后，B 阶段才允许 64 次；效果正负不参与扩容判断。

模型输出依次经过固定 Icarus 规格测试、IR/RTL 一致性与私有规格诊断，再由 `synthesis.py` 对原 RTL 单独综合。结果兼容 `school_bridge.py`，每个学校案例仍由用户在 VDI 登录主机手动执行。`curate` 输出移除会话 ID 的白名单证据及 SHA-256 锁；原始日志仍位于 Git 忽略的 `runs` 目录。

两个候选保留题只离线验证判题器，本轮不发送模型。扩展更多位宽、Mealy 行为或多个时钟时，需要升级 IR/判题协议并创建新版本，不能直接将现有单比特 Moore 结果外推。

## 公开契约的离线验证与升级

`mutation_study.py analyze/run` 只在开发题上枚举固定类别的单处故障，并用图语义和真实 Icarus 核验。生成的 `contracts-v2.json` 明确标注为开发内拟合产物；不覆盖原 bank，不修改历史反馈或成绩。`check` 只消费给定公开 profile，测试保证该执行入口不调用私有 oracle；`verify` 重建枚举、核对源码/输入/结果锁和 DUT 绑定。五种已知 IR/RTL 关系的夹具校准与真实模型研究分别记录。
