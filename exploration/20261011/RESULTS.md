# 首轮探索交付（2026-10-11）

本轮完成14项候选机制筛选、三个有实测结果的离线批次，以及一批实际模型接入尝试。最有价值的新发现是：**增强公开检查在限定两处编辑故障上覆盖良好，但五个延迟触发错误FSM同时通过公开检查与旧固定隐藏测试；独立见证仿真及RTL有界SAT均检出。** 因此下一阶段应同时研究反馈机制和评分证据强度。没有取得新模型RTL，不能给出新增生成收益。

目录根：`E:/Codex/2026-09-25/xzy01-using-llm-for-digital-chip-2/outputs/rtl-batch/exploration/20261011/`。所有下述路径相对于此目录。[候选矩阵](CANDIDATES.md)、[环境](ENVIRONMENT.md)、[独立核验](verification.json)、[历史文件审计](historical-audit.json)。用户原未提交修改、学校脚本/包、历史RTL/提示词/源锁均保留；没有提交、推送或关机。

## 实测与证据

|实验|执行范围与结果|证据|能支持的结论|
|---|---|---|---|
|E1 复合故障|5开发题、3119个不同字段两处编辑；均为语义故障。v1漏176，v2漏0；帮助176、伤害0、其余2943无变化|[plan](runs/compound-v1/plan.json)、[全部候选](runs/compound-v1/cases.json)、[汇总](runs/compound-v1/summary.json)|v2对这批限定复合编辑有效；不能推出任意FSM或自然模型准确率|
|E2 真实仿真/等价变换|每题枚举顺序首10个故障：50/50固定测试失败、50/50IR一致性通过；5正确参考与15重命名/重排/不可达状态变换均通过|[仿真结果](runs/compound-v1/simulation-results.json)、[变形结果](runs/compound-v1/metamorphic-results.json)|证明夹具忠实、公开profile没有拒绝这批语义等价变换；不是自然定位准确率|
|E3 四格模型比较|冻结20槽、gpt-5.6-sol/low、并发2；首4次API_ERROR、0有效RTL、16 pending；HTTP403/workspace routing错误使可靠性门槛不通过|[plan与准确提示词](runs/factorial20-v1/plan.json)、[汇总](runs/factorial20-v1/summary.json)、各jobs/call日志|只有基础设施失败证据，无效果估计、无自动重试；4次应用调用不等于底层请求次数|
|E4 延迟触发边界|按seed20261011构造每题一个12位前缀克隆、共15–18状态；公开v2漏5/5，旧固定隐藏测试漏5/5，新独立见证检出5/5，RTL/IR一致5/5|[执行前协议](DELAYED_PROTOCOL.md)、[候选](runs/delayed-v1/cases.json)、[汇总](runs/delayed-v1/summary.json)|限定单/双编辑的全覆盖无法证明普遍正确；对抗夹具刻意避公开样例，不代表LLM自然过拟合|
|E5 有界RTL SAT|Yosys0.52内建SAT，14步miter，固定初值/复位；5/5反例，轨迹prefix和E4见证逐项一致|[协议](FORMAL_PROTOCOL.md)、[汇总](runs/formal-v1/summary.json)、各题trace.json与yosys日志|在限定时钟tick、初始化和步数下，独立于固定测试找到RTL分歧；非无界证明，不检验模拟异步释放|

E1按题：rt_sequence1209故障/v1漏160；sticky_alarm164/0；event_parity36/0；request_delay501/0；debounce31209/16。五题v2均0漏。每题是统计单位，不能把3119变体当3119独立研究设计。v2例子集合未改动，所有新题仍标开发。没有接触两个候选保留题的内容、隐藏评分或模型实验。

E4新候选在私有评分执行前冻结，没有依据私有通过/失败筛选。每题独立过程oracle核对了长度0–11的4095条输入，共20475条，全部正确；长度12首次错误。表中输出是reset后每个上升沿的采样：

|题族|最短输入|正确输出|错误输出|
|---|---|---|---|
|rt_sequence|111110011001|000000010001|000000010000|
|sticky_alarm|001000000111|000000000011|000000000010|
|event_parity|001110101001|001011001110|001011001111|
|request_delay|011111110000|001000000000|001000000001|
|debounce3|000101111101|000000011111|000000011110|

这些错误RTL在旧评分范围内返回PASS，但有限图明确不等价，现有定位器诚实返回`IR_ERROR_NOT_EXPOSED_BY_RTL_TESTS`。这是一项应保留的“不足以定位”的类别，不应被压成ALL_PASS或SPEC_TO_IR_ERROR。Yosys输出的state在t反映前一时刻的输入：前缀位在step2–13，mismatch出现在step14；[verification.json](verification.json)核对了该时间约定。

## 历史失败再分析

按逐项文件及DUT SHA256确认60 Dev10、24 FSM、32+62配对RTL，共178；另2配对TIMEOUT不含RTL。各实验不同RTL字节哈希数分别28、22、26、49，原样保留完全重复簇。它们只是字节去重，不代替题族或语义近重复审计。总体保存分数159 PASS、10 FUNCTION_FAIL、9 COMPILE_FAIL；本轮没有将重放算新样本。

- Dev10：9编译失败集中在枚举变量三元赋值的Icarus接受性；3功能失败为terra序列位序错误。两者应分别设计语法约束与时序契约实验，不能拿Yosys可综合覆盖Icarus失败。
- FSM：两功能失败在序列重叠回退；table一份可精确定位，prose一份不能做同等自动IR检查。checked_table初始表都正确，旧成绩无法测反馈纠错本身。
- 配对：5帮助对、0伤害对、42双方通过、1基础设施不完整对；帮助只涉及一个保留自然错误及一个人工延迟题族，多次重复不能扩成5独立自然题。旧[paired-audit.json](paired-audit.json)重新校验通过；旧mutation verify确认412文件、163故障、25定位格，通过。

## 资源与预算

离线新增135次Icarus评估（E1/E2：5参考+100故障/一致性+15变换；E4：15），5次Yosys有界SAT；不是135个模型输出。复合批18.235s（5参考校准2.22s）、延迟批2.718s、SAT批4.390s；模型批27.984s。源快照与运行证据核验另约1.5s，不含文献检索/人工编码墙钟。目录交付前约17MB、约1700文件，远低于500MB约束。

模型20槽上限、实际开始4、成功0、失败4、未知结果0、未开始16；失败usage为null，汇总空字典不等于0tokens。input/output/cache、实际服务成本均不可得，标UNKNOWN。CLI内部重连可见，未自行重发研究turn。用户的无限总预算授权不消除服务硬限制，也不授权充值/升级。常见目录/端口未发现可直接用本地模型，未全盘搜权重或下载。

资源实测结束GPU48℃、约1200MiB已用；实验不使用GPU。没有峰值内存、功耗或持续温度记录；没有硬内存配额。单并发离线与双并发模型足够当前规模，没有以低负载代替规模扩展：3119不同复合候选和延迟故障增加了信息量。继续重跑这些固定样本没有新的统计价值。

## 取舍与下一轮三条路线

1. **优先保留：评分覆盖与诊断强度。** 固定仿真、IR精确等价和有界RTL SAT分别报告。下一轮在新开发题族上预声明可达深度、复位插入、边沿间保持、输出拍数与故障模型，验证公开反馈的假阴性以及`IR_ERROR_NOT_EXPOSED_BY_RTL_TESTS`频率。SAT参考应逐步增加独立实现，不能依赖同一转换器自证。
2. **服务恢复后执行：等信息四格消融与等调用重生成。** 本轮四格只建立协议与失败证据，尚未检验收益。不能在旧失败run中悄悄重发；服务恢复后用新run/source锁。四格条件修复仅识别信息/反馈作用，正式研究需新的自然错误题族和端到端第一次生成，加入同一总调用上限的重新生成、确定性IR转换。CLI不能给输出token硬上限时明确仅匹配calls并报告usage。
3. **保留：时序契约规范化与确定性转换。** 从历史位序、重叠和延迟错误选择目标。两组共享相同原始设计事实，规范化不补缺失答案；歧义需独立审核。该路线与[VeriRefine](https://arxiv.org/html/2607.18519v1)、[LLM-FSM](https://arxiv.org/html/2602.07032v1)、[AutoFSM](https://arxiv.org/html/2512.11398v1)、[AoT](https://arxiv.org/html/2505.15873v1)已有机制重合，贡献只能待实验确认，不能宣称首次提出。

暂缓RAG、多审查代理、通用schema大扩展、PPA：目前缺少独立自然错误与最终集，工具建设不能替代研究估计。淘汰“有限公开样例100%覆盖所以任意RTL正确”“调用相同所以成本公平”“重复同题越多所以独立证据越强”三种结论。最终集40题规划、外部审计、作者代码完整复现、自然模型定位准确率、正式端到端改善仍待验证。

## 复核入口

在仓库根，用绝对Python路径运行：

```powershell
& 'C:/Users/A/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' exploration/20261011/audit.py
```

audit只读验证历史文件与四run锁，并维护本目录verification和源快照。执行脚本offline.py、delayed.py、formal.py已完成并拒绝覆盖同名run；模型脚本不会重发已开始槽位。完整源快照在snapshots/<run名>/，原始日志runs/<run名>/，不要将账户原始日志上传或推送。计划与脚本版本改变后必须新建run。
