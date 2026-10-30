# 第25槽剩余商业仿真：一次交付操作清单

用户2026-10-24要求以后尽量一次给全所需操作。当前仅三个尚未执行的独立案例，每条命令一个案例；没有循环、学校调度或自动扩批，不重新执行DC综合或已有Xcelium DC网表。

按顺序在学校Bash终端逐条运行，等待每条返回后再运行下一条：

```bash
bash "$HOME/tsclient/FYP/ECE-Next96/start_verify25.sh" xcelium-rtl
bash "$HOME/tsclient/FYP/ECE-Next96/start_verify25.sh" vcs-rtl
bash "$HOME/tsclient/FYP/ECE-Next96/start_verify25.sh" vcs-dc
```

工具报错、超时或模型哈希不一致时停止，不重复启动。CHECK_COUNT_DIFFERENT表示保留原213门槛而实际检查数量不同；只要正常结束且无工具错误，可继续下一独立对照以定位差异。不得将该状态改写成PASS。

已有Xcelium/DC结果是211检查、0不匹配，1056ps正常结束；原Icarus是213检查、0不匹配，1066ps。原RTL商业复验可区分模拟器/原测试台事件处理与综合影响，但不直接证明时零根因。原题含$random，跨工具输入序列等同性未建立。任何附加观察器或测试修改另立方案，不改原测试或原分数。

三个包分别固定新key和学校HOME结果目录，阻止重复启动。全部原TB/ref字节相同，原RTL与DC网表分别绑定既有证据哈希。门级采用学校同一原Nangate模型（哈希冻结）、TETRAMAX功能分支、关闭specify/时序检查、无SDF。库字节不会回传。每次上限600秒，输出日志及工作盘上限复用已测试bounded进程组控制；每次自动白名单打包回共享ECE-Next96，传输失败只提示ship命令，不再仿真。

准备验收：3包Python3.6语法/输入锁/ZIP字节核验；12判分检查；三组命令源码独立提取核查；Bash语法通过。未运行商业工具，许可证和编译兼容性仍需学校实测。验证文件为offline-verification.json及command-verification.json；包SHA见catalog.json。

VCS版本查询已包含在对应案例，Xcelium同理；无需用户再执行独立版本命令。本次修改只在新包装目录，既有输入和实验代码均保留。
