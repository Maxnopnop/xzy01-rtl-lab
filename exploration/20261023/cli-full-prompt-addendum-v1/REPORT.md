# 完整提示词最终定向排查补充（2026-10-23）

结论：BLOCKED，提前停止。没有第二配置候选，没有新渲染，没有120组验证，没有模型请求、预算/重试实现、升级、认证读取或应用关闭。本次仅运行两个已定位二进制各一次 --version 和 debug prompt-input --help，4次元数据命令，不计模型或渲染调用。

## 核实结果

npm实际二进制0.147.0；桌面实际二进制0.163.0-alpha.11.1。路径、SHA、命令、原始回执见 metadata-commands.json。两个help仅声明输入列表渲染，未列完整request.instructions/tools导出或任意roles/messages输入参数。不能从通用-c接受键值推断任意配置受支持，也不能把桌面历史schema当npm实现证据。

上一轮渲染6个技能源逐一核实存在，其父目录均与 skills.config 中 enabled=false 的目录规范化匹配，6/6。字面文件路径比配置目录多 /SKILL.md；这符合当前官方文档的目录用法，不是已经证明的错误。skill-path-check.json绑定实际文件hash。上一轮目录形式禁用后仍有技能说明，是保留的真实负结果。安装npm包只有JS启动器/元数据/二进制，未发现对应Rust配置实现源码；当前文档不是0.147版本固定说明，因此无法证明该版本目录匹配细节或改用文件路径就有效。不为试出PASS猜另一种路径配置。

现有证据没有支持一个能同时去除技能、权限、环境注入并观测完整instructions/tools的新配置，所以没有使用最后1候选/3渲染额度。未更换二进制进行新渲染，未通过修改导出JSON或为某一模型补提示来统一。

## 不能满足的准确边界

- 原冻结角色system/user；诊断列表developer/user/user，技能、权限、环境附加内容超出冻结正文。
- 基础system正文虽通过model_instructions_file字节hash绑定，最终instructions封装及角色不在渲染列表中，仍未验证。
- 完整tools schema未观察，关闭部分工具不证明tools为空。
- 诊断model_reasoning_effort=low不同于冻结请求省略该字段。此前配置不能直接投入生产；即使后续移除此项，也不能据此认定其他问题修复。本次未改上一包。
- 同模型间列表一致与协议合规是两个条件，前者通过不抵消后者失败。

## 最小接入调整

保持研究协议不变：需要一个支持原始固定system/user消息、统一省略reasoning字段，并能在不生成时输出最终请求instructions/messages/tools封装的可审计适配入口。现有直接API运行器可作为待审入口，但API凭据/模型权限和实际协议支持仍需独立核实；本报告不授权测试或认定API已可用。不能把ChatGPT登录凭据复制成API凭据。

若继续所测CLI而接受附加上下文、角色或reasoning差异，则需要明确修改并重新冻结实验协议，不能在旧冻结包中偷偷放宽。此项尚未获批、未实施。

上轮19项与all20 752项锁均重算匹配，见preservation.json。旧渲染、警告、负结果、原题和RAG均保留。总控可据本补充独立审核后决定接入路线；当前不放行正式实验。

官方依据（本次读取）：https://learn.chatgpt.com/docs/config-file/config-reference ，其中skills.config.path描述技能目录，不能替代0.147源码/运行行为。本机能力证据仅限所保存版本和help，不声称已穷尽所有客户端实现。
