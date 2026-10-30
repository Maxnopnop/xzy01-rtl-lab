# Progress
已只读阅读旧 dispatcher/transport/SETUP 和项目规范。已有 Git 修改保持不动。
read_thread 请求 80000/32000 输出上限被拒绝，未产生网络模型调用；首次 JSON 解析错误保留。工具实际上限20000，原端点输出29885，不能完整恢复。
3份公开目录GET成功保存，无密钥，无重试。新版门禁与240payload/40组、旧封包保全离线通过。
PowerShell初版恢复不存在变量失败：当前.NET null转换空值。原脚本/测试另存；修复为显式存在性记录后12组合通过。模型调用始终0。
默认回归完成：24tests/3fail/1error/2skip，exit1；保持负结果，不修全局runner，不重复测试。launch包准备完成，technical-release仍由总控独立审核后创建。
