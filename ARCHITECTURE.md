# 架构与扩展约定

## 现有模块

```text
batch.py（计划、进程池、锁、续跑、调用上限、报告）
    ↓ 每个样本在独立 Python 子进程中运行
rtl_lab.evaluate（样本证据、生成、提取、固定输入检查）
    ├─ codex_adapter.py：已登录 Codex 直接生成
    ├─ api_worker.py：兼容 Chat Completions 的 HTTP 请求
    └─ backends.SimulationBackend
          └─ IcarusBackend：编译、仿真、统一结果

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

未来加入综合、形式验证、PPA 时建立单独 stage/result，不把仿真 PASS 当成综合或签核 PASS。多文件/多模块设计需要版本化的文件清单和更强隔离，不宜直接取消现有单模块限制。
