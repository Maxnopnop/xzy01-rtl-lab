# FYP：实验与综合验证 — 执行任务书

日期：2026-10-09。总控为“XZY01 FYP 总控”；执行对话为用户授权创建的“FYP：实验与综合验证”。

## 项目与责任

FYP项目根目录 `E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2` 不是Git仓库；实际仓库在其 `outputs/rtl-batch`。进入实际仓库，先读 AGENTS.md、README.md、ARCHITECTURE.md、task_plan.md、progress.md、findings.md、ECE_SYNTHESIS_GITHUB.md 和本任务书，检查Git状态。

总控维护总体计划与FYP缺口；执行对话指导用户学校桌面操作、验收回传并维护独立 `FYP_SYNTHESIS_EXECUTION.md`，避免同时重写三个总计划文件。证据落盘后总控可据文件核查进度，不要求执行对话自动发消息回总控。学校操作由用户在Horizon手动完成，每次给一个明确步骤并等待实际反馈。

保留未提交文件与历史数据。当前HEAD aa6ff55；已有README、ECE_SYNTHESIS_GUIDE和三个计划文件修改，以及FYP_STATUS_AUDIT_20261009.md、未完成elec_*文件。不可当空目录重建工具链。

## 本阶段目标及现状

完成一个保留RTL样本的DC和Genus学校综合验证：两工具分别取得来源明确的执行记录、原始日志、网表和报告；与原RTL、原结果、SDC和库信息绑定，分别审阅。失败与缺失也如实记录；不得为了成功修改原模型RTL。

样本：paired-a32 / m01__real_overlap__s001__control；顶层sequence_detector。Icarus/VCS/Xcelium已有此样本功能测试证据，各1840检查、0错误；不能转用为综合网表正确性证明。

DC X-2025.06-SP2和Genus21.14-s082_1已有学校启动记录。Nangate typical库元数据：1.10V、25C、ns/fF；DB内容、单位和真实加载待验证。两个最新包READY_FOR_SCHOOL_PREFLIGHT，registry imports为空，真实综合未确认。

学校读取Horizon共享ZIP曾超时。最新用户报告：此前在~/Downloads找不到文件，ZIP是否下载到学校Linux及实际保存位置尚未确认。不要重复对不存在的预设路径执行sha256sum，更不能跳过下载/哈希就运行工具。

## 固定来源

- 外层备用包：ece_git_packages/xzy01-synth-local-20261009.zip，26785字节。
- SHA256：13b9b9213082c0e81b0388620fbb92b793a274ceb4319be9f9e84de5113f453a。
- 学校浏览器下载：[私有GitHub文件](https://github.com/Maxnopnop/xzy01-rtl-lab/blob/main/ece_git_packages/xzy01-synth-local-20261009.zip)，点击Download raw file；用户自行登录，不索取密码/token。
- DC包：synth-dc-20261009T100543Z-d47c8919。
- Genus包：synth-genus-20261009T100543Z-07992262。
- RTL SHA256：26bdf79291f1dce79294da4019ddf11287a07bc41041b473c9015b646bc1fabd。
- SDC SHA256：71fd56417922a018fb9dd342d2e310e0dec419672d97123df7fbcbb038f9186e。
- 原结果 SHA256：e64a1cf2e5a93b564cca2a33890f81dd0ac56f79f11e3b0745925465ab48d723。
- 本机已复核两个包输入锁及备用包CRC、哈希；学校下载后的实际文件仍需独立校验。

## 顺序与阶段门

1. **首个用户步骤仅处理学校下载。** 指导用户在学校Linux浏览器打开上面私有链接，下载原始ZIP，确认下载完成及实际路径。已有文件时可先通过浏览器下载列表定位；不要假定文件在~/Downloads。等待实际反馈。
2. 文件实际路径确认后，给一个哈希校验步骤；哈希不匹配停止。通过后解压到新独立目录，核对文件，保留旧目录。
3. 单独执行 `bash start_local_dc.sh`，用户手动运行一个案例。保存启动/版本/库指纹/退出码/执行日志；失败不要盲目再跑或修改冻结包。
4. 回收解压目录returned/中的ZIP与配套JSON，保留学校~/xzy01-synthesis/session-*原始目录。共享不可用时按ECE_SYNTHESIS_GITHUB.md用学校浏览器回传私有仓库独立结果位置。只传已收集白名单，先检查无库/密钥/许可证。完整工具日志保留本机，不将其不加审查全量提交。
5. 使用现有本机导入器核对包、nonce、输入、库指纹、产物及执行记录。逐项审阅DC报告后保存结论。阻塞必须说明实际错误与已尝试操作。
6. **DC证据回收并完成审阅后**，才给用户另一次Genus单例步骤 `bash start_local_genus.sh`；同来源、同SDC、同标准回收审阅。不要将两启动器放在同一命令或循环中。
7. 保存本阶段证据索引与执行日志，指出仍缺功能等价/网表仿真、复位释放、正式时序约束等事项，供总控更新总体记录。

## 验收依据

两工具分别记录：

| 层次 | 必须核对 | 不可替代的证据 |
|---|---|---|
| 工具执行 | 版本、主机、命令、许可证/环境、退出码、完整日志 | 进入shell只算启动验证 |
| 综合输出 | 读取/展开/链接/映射、未解析引用、锁存器、网表及要求报告齐全 | 退出0但缺输出仍不完整；齐全先标COMPLETED_REVIEW_REQUIRED |
| 来源绑定 | 原RTL/结果/SDC/脚本/包哈希、nonce、学校库指纹、PVT与单位 | 不拷贝库字节；不修改模型输出 |
| 报告审阅 | 面积、时序、约束覆盖、违例、豁免和工具警告 | 10ns仅smoke测试；异步复位释放/recovery-removal未覆盖 |
| 功能正确 | 网表仿真或独立等价检查（若尚无则明确未验证） | 原RTL通过仿真不等于综合网表已验证 |
| 时序结论 | 指明库角、单位、约束和报告适用范围 | 正slack不等于签核；功能正确不等于时序达标 |

不新增模型生成、不扩大付费预算、不关机、不上传库或密钥；不用SSH或学校批量调度。不创建新对话或向其他对话发消息，除非用户另行授权。

## 后续研究缺口

本阶段是工具链验证，不能增加历史模型样本数或证明方法提升。独立最终题集、端到端及等信息/等预算消融、自然错误定位验证、最近邻差异、队友独立复现和论文材料仍待后续规划，见FYP_STATUS_AUDIT_20261009.md。本阶段不要并行扩大研究实验。
