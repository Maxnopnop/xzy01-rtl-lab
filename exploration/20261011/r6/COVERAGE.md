# 规则→见证→公开/隐藏/边界矩阵

矩阵记录存在的轨迹和已知缺口，不以向量数替代覆盖证明。public仅每题一个手算轨迹（见REFERENCE_AUDIT），private含12条28-cycle固定随机、定向短轨迹及独立中途reset版本；正常轨迹不被强制中途reset截断。所有事件在#2取样，binary输入。

| 规则 | 见证/路径 | public | hidden与边界 | 缺口/不可观察 |
|---|---|---|---|---|
| 队列乱序完成不改变退休顺序 | issue1/2，finish2/1，空拍退休1/2 | 手算7拍 | 全4×4 issue标签配对，正常7拍连续退休 | 非所有状态×输入交错；内部空槽残值不可观察。 |
| 旧满容量/旧重复拒issue | 满队列已ready同时issue3仍拒；ready头旧tag再次issue拒 | 满队列见证 | 定向重复tag/finish竞争5拍 | 未证明长无限issue无饥饿；未知finish忽略主要由随机检查。 |
| 新接纳当拍不能finish/flush优先 | 空队列issue1+finish1→未ready；flush+issue+finish→全清 | 未公开所有组合 | 两条固定5/3拍见证及随机 | 定向不是组合穷尽。 |
| 除法四次advance、pause、busy忽略start | 13/3四advance，中间pause，末拍start8/2忽略 | 手算7拍 | 全16×16 operand正常路径（含d0），额外busy-start/abort、pause/末拍start | 全operand无暂停结果有限域穷尽，不覆盖全部时序交错。 |
| 除0立即完成/abort优先 | d0→q15,r=n；busy abort+start+advance→清 | 未公开d0 | 16种d0与定向6拍abort | busy时长暂停无限性质未证明；新accept保持先前非零结果无独立手算见证。 |
| join捕获与匹配分拍、blocked保持 | A1,B1→下一拍move；输出满时等tag停，take替换 | 手算8拍 | 全4×4标签对；额外7拍match/block/clear | 同拍旧满槽新valid替换竞争没有单独手算；随机覆盖不能称穷尽。 |
| join不等丢小tag、clear优先 | A0/B2丢A；对称tag对丢B；clear+take+valid全清 | A小tag见证 | 标签配对对称方向+固定clear同时事件 | 无跨tag模序号解释，标签为明确unsigned排序；不测循环wrap协议。 |
| falling/高低稳定保持 | 每cycle low_hold/rise/high_hold/fall，high时翻转最低输入bit | 全public | 全private + fixed随机多位变化 | stable low同多位突变由跨cycle测试；非模拟模拟毛刺/亚稳态。 |
| async assertion/release | reset_low/release_low；第3/8拍中途reset，稳定同level release | 初始低reset/release | 独立reset版本包含高/低中途assert/release；end_reset | 非analog reset recovery/removal签核。 |
| 格式与大小 | 多code block/128KiB+1；256KiB exact/over | 工程人工 | control/recovery/process分别封存 | 非模型服务上下文接受保证。 |

既知不可观察/未证明：未暴露寄存器编码及不可达内部值；除法两个不同内部算法只在可见输出/发布时间比较；没有形式工具的无界证明、PPA/综合签核、多时钟CDC、X/Z输入或任意参数。题目固定小参数，最长输入序列28个常规rising周期（另有复位准备边沿），不把重复数或不同seed当独立最终集。
