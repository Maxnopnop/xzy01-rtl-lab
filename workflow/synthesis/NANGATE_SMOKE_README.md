# Nangate typical 单案例综合验证（2026-10-09）

库元数据由用户从学校 Liberty 文件读取：NangateOpenCellLibrary，typical，process=1.00，1.10V，25°C，时间 ns，电容 fF。DC 的 .db 内部单位尚未由工具核对。

样本：paired-a32 / m01__real_overlap__s001__control，顶层 sequence_detector。
本轮复用历史 RTL，不生成、不修改 RTL。两工具使用相同 RTL 和 SDC；包有独立来源哈希。

SDC 是 Codex 根据源代码审阅后设置的流程 smoke 条件：周期10ns，时钟不确定度0.1ns、转换0.1ns，data_in 输入延迟0..1ns，sequence_detected 输出延迟0..1ns、负载5fF。数值是明确的测试假设，不是项目性能要求。rst_n 为低有效异步复位，本轮从其端口设置 false path，不覆盖复位 recovery/removal 或释放安全；不能用于签核。

每次手动执行 start_dc_smoke.sh 或 start_genus_smoke.sh 只运行一个案例。运行前检查库、环境和输入哈希；运行后自动收集白名单输出并回传到本共享目录 inbox。尚未执行真实综合，Tcl/SDC 在学校版本中的接受情况、DB/Liberty 对应性、单位和时序报告均待核对。

若本机 GUI 已打开，请先保留未保存输入，再重新打开以加载新配置。此 SDC 仅适用于选定样本，不可对其他接口直接复用。

SDC 基础语法参考：[官方 create_clock 文档](https://www.intel.com/content/www/us/en/docs/programmable/683243/25-1/create-clock-create-clock.html)。厂商实际接受情况以回传日志为准。
