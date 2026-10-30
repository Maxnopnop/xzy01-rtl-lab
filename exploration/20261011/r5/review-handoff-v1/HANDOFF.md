# R5 中断收尾：总控审核材料 v1

本包只新增只读复核与中断诊断，不修改 R5 原版本、封存证据、成绩或旧实验。用户授权交总控审核；审核完成前不决定或执行后续采样。

## 中断原因与证据边界

北京时间 2026-10-11 14:12:28.461755，第 21 个槽位 `escape_frame__r1__structured__regeneration` 写入预约。14:12:30.275 出现 IPC EPIPE；14:12:30.456–.457，本地 stdio app-server 停止，日志明确记录 `cause=stop_process`、`hostId=local`、`next=disconnected`。15:20:59.887 新桌面实例启动 app-server，15:21:00.242 记录 Launching app，15:21:00.987 本地连接恢复。

已确认的机制是桌面本地 app-server 生命周期停止及之后的新实例启动；与未知预约相隔约 2 秒，支持本机基础设施中断解释。**停止的触发原因仍未知**：现有日志不能区分手动关闭、重启、更新、崩溃或其他触发，也未证明该次 CLI 子进程的具体终止路径。不能把关联写成已确认的根因。

Windows 在 14:10–14:15 窗口内未查到所筛选的应用崩溃/挂起及系统电源/关机事件；这只是该查询无匹配，不能证明没有崩溃。原收尾和本次进程检查均未发现关联运行器；会话 55896 已不可恢复。桌面 thread API 仍返回旧 turn 的 inProgress、无 completed/error，状态与已消失的进程不一致，不能据此判断调用仍活跃。

已有 durable websocket 403 属于另一连接通道，不足以把第 21 次调用归因为模型/API 403。20 次已知 CLI 返回均无 error/turn.failed；第 21 次没有可供归因的 CLI 返回。此次没有重试 403。运行器在子进程返回后才保存其返回日志，因此日志缺失也不能证明请求未抵达服务端或没有消耗。

诊断依据为 [local-lifecycle-evidence.json](local-lifecycle-evidence.json)、[windows-events.json](windows-events.json)、[current-process-check.json](current-process-check.json)、[thread-status-snapshot.json](thread-status-snapshot.json)。生命周期证据只摘录 11 行，保留源路径、行号及行哈希，不导出整份日志/对话。日志来源选择参考 [OpenAI 官方故障诊断文档](https://learn.chatgpt.com/docs/reference/troubleshooting)；具体原因判断来自本机证据。

## 20 / 1 / 27 核对

| 类别 | 数量 | 复核依据与处理 |
|---|---:|---|
| 完整返回 | 20 | 20 个不同 CLI thread，每个恰有一个 turn.completed；进程 returncode=0，无 timeout/output_limit/killed，无工具调用和 error/turn.failed。20 个生成结果原判 PASS（3 IR、17 RTL）。 |
| 未知预约 | 1 | started.json 存在；恢复记录 UNKNOWN_INTERRUPTED、usage=null；缺少 codex.json、stdout 和最终模型输出。保持未知，不重发。 |
| 未启动 | 27 | 没有 started.json 或 generation.json；保持 PENDING，不补样。 |
| 固定计划 | 48 | 20+1+27=48；每策略主分母仍为 6，不能用已返回子集替换。 |

终局 S-R 为 2 PASS / 1 UNKNOWN / 3 PENDING；S-F、D-R、D-F 各为 2 PASS / 4 PENDING。完整 phase_snapshot 子集不代表三任务族总体成绩；自然 stage 错误样本缺失、反馈无变化等负结果及默认代理回归失败均保留，不能据此宣称 IR 或反馈有效。

## 费用账

已知 20 次的 usage 为 input **226300**、output **6156**、cached input **126208**、cache write **0**、reasoning output **744**。cached input 是 input 内的缓存部分；reasoning output 是 output 内的子集，均不得重复加总。

| 策略 | 已知半共享 input | output | cached input | reasoning | 已预约半共享调用 |
|---|---:|---:|---:|---:|---:|
| S-R | 56549.5 | 1603 | 29696 | 336 | 6 |
| S-F | 56633.5 | 1603 | 37120 | 336 | 5 |
| D-R | 56516.5 | 1475 | 25984 | 36 | 5 |
| D-F | 56600.5 | 1475 | 33408 | 36 | 5 |
| 合计 | 226300 | 6156 | 126208 | 744 | 21 |

半共享已知完成调用为每策略 5，合计 20；S-R 的额外 1 为未知预约。计划每策略 12 个半共享调用、18 个机会，不能冒充实际调用数。第 21 次服务端 usage 未知，整批 provider usage 与金额均为 **UNKNOWN**。原汇总的缺失 usage 保持 null，不能填 0；本包不根据标价推断账单。

## 保全与审核请求

新脚本 [audit.py](audit.py) 只读取原证据并写入本目录。复核原 results packet 11 项、运行封存 869 项（同时检查精确文件集合）、准备封存 2175 项，全部哈希匹配；原 source/version/score 未改。此前收尾已核对 33 源码/资产、8066 旧绑定和 4860 R4 封存文件，本包通过原 results packet 哈希绑定该收尾结论，未重跑旧实验。

请总控独立核对上述 20/1/27、费用子集及分母、未知保留、中断原因的事实/推断边界，并核验本包 [verification.json](verification.json) 与原 `../RESULTS.md`、`../actual-analysis.json`、`../results-packet-lock.json`、`../runs/prepared-v1/evidence-lock.json`。审核意见应另写新文件，不覆盖原证据。

本包新增模型调用 0、模拟调用 0；没有重发未知调用、补样、403 重试、改成绩或释放下一轮。审核后再决定下一步。
