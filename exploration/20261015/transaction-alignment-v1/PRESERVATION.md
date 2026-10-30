# 旧证据保全及新执行隔离

准备脚本只读取并验证v2 prior全部旧绑定，以及v2/补正已冻结包的源/原run/结果；新prior-lock纳入这些字节、原R6 prepared-v2源锁及计划、新工具文件信息。不会写旧目录。默认负回执仍是v1的24tests/3fail/1error/2skip exit1，新v2全条件15/16、类别预声明不符、校准exit1；它们不会被本次新预期覆盖。v2原native证据与补正先前已被总控分别接受，不重复旧审核/工具执行。

- v2原包 SHA：c614a32526e2fa0cb182be7b9dde7aca6e6249df54169a2b190da1f5569eaf16。
- 设计补正 SHA：090fa59f73bc8355a52d15fc7158e368a6fa94e7c6355a962c4043baf975f012。
- R6 prepared-v2 plan SHA：f5c7793ad63cccde246ba9b81e28b1aab0c1bdec9c02b407207094d9a21db7b4。
- R7旧包 SHA：b2f63e5db433bc0a099574b65ecfffec30c787141741b11b3cb0126414cf506e（在旧绑定内，未扩候选）。
- v1握手包 SHA：d060a32dba45329046e7a71cf5b3c687fccc874bbaede47415bad3d3c9de268a。

本目录spec_checker.py与v2 checker逐字同SHA；新RTL从v2开发结构另复制，新增延迟参数只影响新目录；新IR不来自模型。当前R6 intent源及输入输出overlay/AST插桩分别锁定，原intent/tasks/runner不改。具体行号源快照见current-ir-source.json与已保全的设计补正source-snapshot.json。

tools.json只读顶层exe文件SHA和Windows版本元数据。Python PE版本可读；Icarus/vvp PE版本缺失为UNKNOWN；未运行--version或旧compile/sim来获取。没有完整冻结工具安装树/所有动态库，这一点是复现边界；阶段B每process记录argv及顶层exe SHA，不可声称工具链全部传递依赖已冻结。

阶段A Python仅运行freeze.py的文件/JSON/AST检查；目标IR模块parse/evaluate/run、新harness评分/driver函数、IRworker、Verilog编译/仿真、default、模型均0执行。不可把本机Python用于静态脚本误报为IR运行，也不可把静态AST通过误报为功能通过。

完成阶段A后只允许在新run-v1写执行证据（仍须新精确SHA批准），不改准备源/计划；run不属于准备包。源变化或预声明不符立即停留原失败，不自动创建v2或补运行。总控审核前本目录没有run-v1，PREPARATION给出尚未执行状态；INDEX是本线程允许的公共索引追加，根计划/学校任务保持。
