# 显式Astrill代理新36槽总控验收

2026-10-29用户明确要求“重新开始36次实验”。此release仅新36，不是旧槽重试或剩余35接续。保留旧UNKNOWN1和HTTP4031，累计最多38次机会。

## 结论与证据

通过用户手动执行准备验收，尚未调用模型、未验证真实OpenRouter推理可用性。

- `binding-audit.json`：22项旧证据hash基线保持、874冻结包文件保持，36请求原始字节/模型不变，六组同题同条件完整messages一致，新ID全部唯一且未预约。
- `connect-audit.json`：冻结transport显式代理6项独立mock，通过代理地址127.0.0.1:3213、CONNECT目标openrouter.ai:443、五HTTP状态单POST，以及代理失败无重试无直连fallback。未使用真实socket。
- `replay-tests.json`、`replay-tests.txt`：总控另目录重放28/28通过，探索原28/28也通过。模拟完整36顺序运行、旧release拒绝、跨入口预约防重、崩溃/保存失败后不重启、服务身份错误/工具错误/检查数异常停止、原请求不加token上限、代理环境不继承与路由篡改拒绝等。模拟数据不作模型收益证据。
- 正式PowerShell `-Action Preflight` 退出0：756实际路径写读通过，最长157字符；Icarus路径与Ubuntu Yosys可找到，0网络、0EDA启动。PowerShell隐藏输入一次/清理恢复密钥源码和离线入口证据已核查。
- runner相对旧r2仅新增明确路由及双父批次绑定、新ID/累计38计数及新release门禁；原请求/判断流程不改。

## 放行

`release.json` SHA256 `fecda92fdb21d74a1c54b8bb134630dad7303ff551f2b213ed1678dba1a4981c`。

仅 `rag36p1-001..036`，三题055/124/072，4o-mini/4.1-mini/5.6-luna，有无RAG各2样本。source-lock-r1、batch、父证据、offline-audit-r1、route-config均绑定；旧包、旧release和300草案不放行。新批次由用户一条命令手动启动，输入一次key，最多36次顺序调用。正常功能/编译失败继续，服务/未知/工具/检查数异常停止，无自动重试、补样、扩批或重启。

显式代理127.0.0.1:3213，不读取ambient代理，不改系统/Astrill设置。公共GET出口诊断不能证明OpenRouter地区访问资格或保证403恢复。若仍403，保留并停止。

calls_only无token/美元硬cap，无批次总截止；保留单请求180秒超时。旧两次费用未报告，不能将缺失视为0；实际usage/cost按原回执记录。参考同源非独立oracle，模型默认计算量不等。此入口不启动学校四工具；后处理沿用本机Icarus/Yosys。
