# 超长prompt离线CLI传输补验与v3审核交付

**原argv路径确实无法发送本批长prompt；独立v3改用UTF-8文件重定向stdin，离线字节传输验收通过。** 本轮真实模型调用0、真实CLI生成调用0、RTL仿真0；只运行真实CLI本地version/help命令。没有重试403，旧版本/证据/成绩保持不变。默认代理回归仍失败，原日志与新增失败均保留。

## 实测问题与修复

旧codex_network_adapter把完整prompt作为末尾argv参数。复用它的命令构造及真实Windows CreateProcess，仅将可执行体替换为本地Python CLI接收夹具：16个v2分支prompt中4个短prompt送达，12个长prompt均在进程创建时发生WinError206，没有接收收据。多代码块及ASCII/UTF8 131071/131072/131073字节候选的完整原文保留，失败不是判题格式分类问题。

新增独立目录r3-runner-v3，未修改v2：cli_adapter.py保持原版本/登录检查、模型/禁工具参数、事件解析和代理行为；末尾prompt参数改为单独 `-`，prompt按原UTF-8字节保存，stdin_process.py将该文件直接作为子进程stdin。沿用原壁钟/输出上限/进程树清理实现；没有截断、换行规范化或将候选拼成shell命令。runner.py只切换新adapter和新准备门槛，继承v2的role/judge.stage隔离及EXTRACTION_ERROR分支分类。

实际安装CLI的help说明 `-` 从stdin读取指令；本地help/version日志及可执行体SHA保存于runs/transport-v2。测试不执行真实Codex生成或登录检查，夹具中的登录/事件/回答为明确标记的固定工程值，usage为0。

## 验收与独立核验

成功run：`runs/transport-v2/summary.json`。通过新runner.generate→新adapter→真实Windows子进程，复用v2验收已保存的全部16个两臂prompt，逐字节核对原prompt、exact-prompt、adapter文件、接收文件；接收长度、SHA256、nonce及末尾argv `-` 一致。完整ASCII/UTF8边界候选均未截断。另有1048609字节混合CRLF/LF、中文、emoji、引号、反斜杠与shell敏感字符测试，以及空白/EOF测试。新命令长度均低于Windows限制。

非零退出、超时树清理、输出超限均被记录为API_ERROR；运行器保存失败后再次进入不会重发。没有mock Popen/文件读取/OS运输，只替换CLI可执行体和离线环境路由，网络环境不进入夹具。该结果证明离线父进程到CLI兼容接收子进程的完整运输；真实Codex生成、服务端token/context接受能力未验证，不解释为模型效果。

父目录v3-verification.json独立核验通过：33源码绑定、16个分支字节绑定、nonce及三个负分支；成功run封存585文件，首次失败run封存35文件，回归2文件。历史与v2合计7419个证据/来源绑定逐字节不变，包含旧默认代理失败日志和旧隔离通过日志。

## 负结果保留

- `runs/transport-v1`：首版测试夹具提前创建call目录，runner.mkdir触发WinError183，首个短argv已送达，新stdin未执行。保留失败说明、证据锁、脚本及当时源码快照；其旧源码锁按快照核验。修正测试另存transport_acceptance_v2.py，详细变化见AMENDMENT.md。
- 原argv的12次WinError206全部保存在成功验收run的original-argv各目录，并计入汇总。
- 按AGENTS对有意义的新运行器变更运行原34项回归，默认代理及原测试未改：3 failures、1 error、2 Yosys环境跳过，两个loopback方法仍失败。新增完整日志runs/regression-v1/unittest.log与summary.json封存；本轮不隔离代理或重试失败方法，不声称全回归通过。

## 审核入口及未执行计划

新源码：runner.py、cli_adapter.py、stdin_process.py、judge.py；夹具cli_fixture.py和transport_acceptance_v2.py；冻结协议PROTOCOL.md及执行补记AMENDMENT.md。主证据runs/transport-v2/evidence-lock.json；独立核验父目录v3-verification.json。

新24槽计划已prepare/verify，全部未启动，SHA256：`50c9e29dff46e590471a21f65ac2329f75f6213ea7049b5f7a59f1c402867a75`。旧v2计划及成绩不改。本次仅提交工程审核，不请求启动模型；即使后续审核通过，真实模型执行仍须明确放行新冻结计划。

## 总控复核后的终止范围限定

上文“超时树清理”表述收窄为：超时/输出超限触发既有kill_tree，并确认直接接收进程结束。negative/*/codex.json中的killed及非空returncode支持这一直接进程终止结论；timeout夹具只sleep，overflow夹具也未派生子进程，本批没有后代进程存活/退出见证。因此，后代进程树清理未在本批独立验收，不能将沿用kill_tree代码等同于完整进程树清理实测通过。本限定适用于本批报告中的相关“树清理通过”表述。

仅在冻结run外追加此说明；原负结果、源码、协议、证据锁及成绩不改，无新增测试或模型调用，24槽计划仍未启动。
