学校 VDI 手动复核包。通过共享文件夹复制到 Linux 家目录。
每次进入一个案例目录，执行：tcsh run_xcelium.csh
不要在共享 VDI 上循环批量执行。脚本路径来自已有资料，可用 VCS_SETUP / XCELIUM_SETUP 覆盖。
将完整案例目录复制回本机，保留源码、向量、退出码和日志。
本机导入：python school_bridge.py import --package 原始导出目录 --returned 回传目录
VCS/Xcelium 脚本尚需在学校对应版本上实际验证。本机离线验收不等于商业工具验收。
