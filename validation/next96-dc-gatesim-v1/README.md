# 第25槽 DC 网表功能仿真：准备完成，学校待执行

用户要求先完成前项DC网表功能验证。本包只允许第25槽DC网表的一次Xcelium测试，不重跑DC，不启动VCS或其他样本。原RTL的VCS/Xcelium对照及VCS网表验证仍在后续待办。

学校Bash命令：

```bash
bash "$HOME/tsclient/FYP/ECE-Next96/start_dc25_xcelium.sh"
```

启动器校验ZIP后复制到学校HOME独立目录，核对原输入、DC网表和Nangate模型哈希，再单次运行xrun。需要的商业工具环境和许可证仅学校运行时才能验证；本地离线通过不代表已商业仿真通过。

包：next96-dc-slot025-xcelium-v1.zip；SHA256 fed1ea064516d06a18dc57a755a3ef767637927ff2661623d327b33205d3e7ca。共享C:/Users/A/Documents/FYP/ECE-Next96。结果固定学校目录~/xzy01-next96-checks/next96-dc-slot025-xcelium-v1，拒绝重复执行。模型留在学校，不打包或回传。回传包在同一共享目录，名称return-next96-dc-slot025-xcelium-v1.zip及.json。

本机检查：10项包/语法/判分/防重/篡改检查通过，Bash语法通过，2项合成进程测试（正常退出、超时杀进程组）通过。0模型、0商业EDA调用，不改原题、RAG、RTL、测试台、参考和DC网表。

判据：工具成功退出、恰好一条Mismatches行、213检查、0错误才为FIXED_TEST_PASS；保留功能失败、分母变化和工具错误。原题采用$random，跨模拟器实际随机序列不能假定相同；原采样代码未改变，调度或delta-cycle差异应另行诊断，不能默改测试修正分数。

功能模式沿用历史已校准Nangate模型SHA256与TETRAMAX宏分支，-nospecify，无SDF。这不是TetraMAX工具或时序仿真。新增测试不代表完整形式等价证明。

用户学校只读输出确认typical.lib time_unit=1ns、capacitive_load_unit=(1,ff)，面积单位仍未得到明确字段。此次不重做DC报告，不更改综合约束。
