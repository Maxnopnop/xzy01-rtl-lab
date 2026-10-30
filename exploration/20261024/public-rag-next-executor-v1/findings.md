# Findings
旧core固定BATCH旧20及240，不能直接用于新批。复用transport发送实现与usage_record、冻结A的extract_rtl；新账本隔离。
按本轮资源错误即停要求：文本超过128KiB必须RESOURCE_LIMIT停；工具timeout/原TB TIMEOUT亦停；普通模型RTL编译失败保留结果可继续。只改变新执行控制，不改任务/方法。
原TB/helper、X屏蔽、multi-hot覆盖缺口与条件标签继续保留；reference alias校准不等于独立正确性。
