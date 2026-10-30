# R5规则—见证—覆盖矩阵

规格来源tasks.py文字；过程参考tasks.step；手写SV references/*.sv；不同推导reference_alt.py；手推状态runs/calibration-v3/anchors.json。公开/私有期望均为过程oracle输出，交叉核对不能排除共同误读，未有外部独立作者审阅。

|规则|有区分力见证|冻结路径/覆盖|未覆盖|
|---|---|---|---|
|phase只有fall采样，rise使用旧sample|rise publish/data2→visible0；fall capture3→sample3；rise publish/data1→visible3|anchors.phase前3；public首序列；私有随机及输入枚举|参数变化、模拟非零建立保持时间|
|phase clear高于capture，publish脉冲仅rise更新|fall clear+capture/data2→sample0；fall保持published|anchor4/public序列；priority-mutant公开/隐藏FAIL|瞬态/亚稳态|
|escape控制token在escaped时为payload|START ESC gap END DATA END→last_sum2/count2|anchor6状态；public第二序列含gap+escapedSTART；第一序列含escapedEND；突变公开/隐藏FAIL|无限帧长；binary之外|
|escape START重启、ESC不累加、END提交、flush优先保留last|公共两序列、私有random24和全部packedinput三步序列|同作者文字/oracle/两参考；已冻结|所有可达状态×所有命令非穷尽|
|allocator release先于alloc，满时可同拍重分配|连续4分配，满reject；release_id2同时alloc→mask15/hint3/last2|anchors第5/6，public首序列；私有枚举；SVloop vs集合距离推导|动态容量/参数/无界安全性质|
|allocator稀疏搜索，hint更新chosen+1，release任意洞|释放0再从hint3分配→last0/hint1|anchor7/8；hint+1突变公开/隐藏FAIL|公平性长期活性证明|
|所有注册输出稳定高/低输入变化保持|private每单input bit翻转后恢复、public全反相|high_hold_bit/low_hold_bit；phase合法fall单独建模|#2采样前glitch、X/Z输入|
|异步中途reset高/低断言及稳定level释放|private第3cycle high断言/release无边沿，第6cycle low断言/release无边沿|midreset_high/low、release_high/low_no_edge|模拟窄脉冲、复位与边沿极小时间差；所有输出只#2观察|

每序列从低clk reset初始化；最高24循环，私有第3/6循环复位，此后最多18连续循环。全packedinput值三步测试不等于全状态乘输入穷尽。另12固定seed随机24循环/任务，phase有rise/fall独立输入。public/private事件数见assets/coverage.json。不以向量数量证明覆盖完整。无需重判旧R4模型样本。

无大规模突变枚举，仅三核心优先级突变用于确认判据敏感性；三人工正确IR/确定性转换为校准，非自然错误或模型增益。
