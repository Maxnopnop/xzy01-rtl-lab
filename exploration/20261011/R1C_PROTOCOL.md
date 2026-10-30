# R1c 中途复位与边沿间保持（执行前）

2026-10-11。新增timed_reset.py、runs/timed-reset-v1；不改变R1/R1b任何源码、协议、成绩或核验文件。只运行Icarus时序事件，不用async2sync，测离散RTL事件而非模拟物理复位。

5开发题，独立Python过程oracle维护已采样输入/复位历史。所有长度0–5二进制前缀分别驱动后，在clock低/高两相位进行三类中途reset：无posedge的短脉冲（保持一个检查间隔）、保持跨posedge、reset与posedge同拍；active-low，输入在reset时为0/1。reset后继续固定尾串100110010110，再做保持检查。每个正常周期在clock低与高各将din翻转再恢复，检查q保持；fallingedge也检查不更新；release reset无posedge时检查保持reset输出。所有样本同事件profile、期望值由过程oracle给定，公开例子不参与调优。TB每事件留#2 settle采样，无时间零/零delay竞争。它不证明recovery/removal、亚稳态或任意模拟窄脉冲。

先校准：5独立过程RTL正确参考PASS；event_parity人工sync-reset、reset忽略din=1的优先级错、组合din泄漏、negedge更新四例FUNCTION_FAIL；真实语法错误COMPILE_FAIL。共10次Icarus评估，诊断必须有phase/category/expected/observed，校准不通过不得历史评分。

历史选择在评分前固定：FSM48及paired-A/B中上述5题原PASS，按task/model分层轮转路径顺序，全球RTL字节hash去重，上限64份；同hash的其他来源另保留别名，不当新样本。所有原result/RTL hash锁定，原字节复制。原FAIL不进入主要新错误指标，先前校准错误夹具不算自然样本。若全部独特输出少于64就取全部，不用重复补数。无需参考模型RTL，历史判题只用过程oracle及固定事件向量。

主指标：原PASS中新增FUNCTION_FAIL；环境/编译/timeout/unsupported分开。每份第一次不一致阶段与输入事件保存；新错误需同一原DUT、最早失败事件前缀另建短见证TB再独立重放，原固定分数不改。负结果保留，不看隐藏评分挑题或修候选。统计单位5开发题族，不把64输出/数万事件当独立题。

资源上限：最多10校准+64历史+64复现Icarus；compile15s/sim10s、CPU顺序1、总墙钟10min、目录200MB；没有硬内存隔离，仅已有受限单模块RTL；连续3环境错误停止。无模型调用/403探测、GPU0。达到校准和冻结样本评分/复现后结束，不无限扩展。
