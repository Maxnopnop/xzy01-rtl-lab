# 外部参考依赖审计

axis链：Alex README/RTL→同作者Python COBS算法或帧关系/struct解包→cocotbext-axi或MyHDL axis_ep握手收发→received-frame assert。作者与本项目独立，但文字/实现/原测试仍可能共同误读；COBS算法不同抽象并非外部第二作者。模块1/3/4/6/7保存原测试不固定所有微架构波形，无法把implementation波形直接当成word-spec完整golden。原test只是阅读，cocotb/MyHDL/axis_ep完整依赖未执行，不能给官方测试PASS。

cells链：README/头注→各外部作者RTL→cc_pkg/registers/assertions宏或cc_sync_wedge/cc_lzc依赖。其作者署名与项目作者不同，依赖正确性、原test独立性与Icarus全配置可执行性未验证。9/12在前置近重复家族关卡排除；10双时钟排除；11原路径身份404未解，不为无用编译下载整个依赖库。

本项目新TB只检查两个手推见证，没有另造完整黄金oracle。广播见证直接观察valid0的payload变化/valid1广播/背压/中途同步reset，不使用原RTL波形自动导出期望。无效payload置零的功能等价变换表明精确逐拍判据可能误报；这是有限见证，不是验证任意新流水线都正确。并未新增生产mask/checker。

stat_counter原文说counts frames，源在last分支只frame_next=0，非last且旧frame0才加1；singlebeat last在8bit计数配置下byte01/frame00。原MyHDL例有多拍17字节数据，不能替代单拍覆盖。原观察原样保存，定性为待解规则/参考冲突，不先宣布作者bug，不修ref或写新的假权威规则；因此不纳入。

source-calibration-v1：2原compile、2sim退出0只说明观测复现。stat帧数0是负向参考观测，不能因进程exit0称参考功能PASS；无模型收益、无自然stage错误。未做全状态/交错事件/无界证明/模拟CDC/PPA。完整receipt包含argv、source/TB哈希、原stdout/stderr及二进制。
