# Xcelium/DC第25槽：回传存在检查分母差异

已核验共享return-next96-dc-slot025-xcelium-v1.zip的sidecar SHA、无重复且白名单ZIP成员、payload-lock与所有输入原字节。回传位于returned-v1。Xcelium 23.03-s004，退出0，6.479秒；Nangate模型哈希等于冻结值7b80af03f2ed72d40f014b836b13526aff3f64105415587c74f2260588b74363。只有SPDUSD未使用include目录警告，未见编译/展开错误。

真实结果：Mismatches: 0 in 211 samples，正常由原testbench.sv第44行$finish在1056ps结束，非工具超时。三个输出均无已观察到的错误。保留CHECK_COUNT_DIFFERENT，不能改写成满足原213检查门槛的PASS。

本机原RTL及Yosys网表：0/213，结束1066ps；学校DC网表Xcelium：0/211，结束1056ps。原时钟每5ps翻转，差值10ps为一个周期，对应两个边沿检查。原测试台时钟初始化为0且stimulus先等待negedge clk；跨工具是否将时间零初始化计为该等待事件是可能解释。缺少初始化事件的原始时间轨迹，不能声称根因已证明；也不能据分母差异判RTL错误或私自修改测试台。

下一有区分力的已有授权检查：同一Xcelium运行该槽原始RTL，原testbench/reference保持字节相同。若原RTL也211/0且1056ps，则更支持测试台/仿真器事件处理差异而非综合引起；仍不等于逐事件输入、波形或形式等价。公开TB含$random，跨工具不保证相同实际随机输入。VCS原RTL/网表验证另待继续，不自动扩批。

本轮只读验收0模型、0EDA，没有重试该DC网表或修改213门槛。
