# 一次有限外部来源筛选预声明（检索前，2026-10-15）

人类授权已在总控read_thread核实。只做来源/参考/时序契约静态审查，不执行任何候选IR、编译、仿真、模型或旧重判；不改方法迎合候选。固定两个新来源项目和六候选，失效/缺路径/排除均占分母，不换源、不补候选，零入选也交付停止：

1. lowRISC/opentitan，hw/ip/prim/rtl/prim_packer.sv，数据打包。
2. 同库，hw/ip/prim/rtl/prim_alert_sender.sv，差分alert握手。
3. 同库，hw/ip/prim/rtl/prim_esc_sender.sv，差分escalation握手。
4. freecores/i2c，rtl/verilog/i2c_master_bit_ctrl.v，I2C位控制。
5. 同库，rtl/verilog/i2c_master_byte_ctrl.v，I2C字节控制。
6. 同库，rtl/verilog/i2c_master_top.v，Wishbone/I2C顶层。

先锁各库默认分支commit，获取该commit目录树仅定位上述路径、许可、规格、参考/测试及必要依赖，不把其他树节点转成候选。若这些预猜路径不存在，记ORIGINAL_PATH_UNRESOLVED，不移到类似模块补位。sourceURL固定后最多一次访问；403/404/超时/其他错误都保留，不同失败URL不做轮询重试或换代理。最多48次本机来源HTTP访问，最多36个原文件，每文件512KiB、总原文件8MiB；树JSON仅元数据≤8MiB，Web只用官方GitHub项目检索索引并记录查询。必要规格/引用资料不算新候选项目，不增加第三候选源。

纳入为可进一步审查需：来源commit/许可/原字节清楚，项目历史未调优及近重复审查不过度承诺；文字规格不从实现偶然波形反推；参考可信度、独立性和时序覆盖各自足够，当前IR/适配仍有明确域边界。本轮不授予final heldout资格。候选实现本身不能同时当独立golden；同库DV/测试也不自动等于独立作者参考。缺可信参考/契约/独立性则排除执行，若有信息价值最多推荐两个待审有限验证项（非入选）。

历史排重覆盖custom20/Dev10/paired/FSM/R1–R7、握手v1/v2/事务对齐人工源与结构机制。R7的verilog-axis/common_cells及其近重复、FIFO/仲裁/弹性槽/广播等已开发机制不改标独立保留集；本轮项目未调优不保证训练未见。无法查清项目早期访问或他人工作副本标UNKNOWN；本轮开始后的所有阅读记录暴露，未来方法若据此改动即development。最多按机制多样性及当前既有域兼容程度给两项条件建议，不因外部数量或人工检出宣称研究收益。
