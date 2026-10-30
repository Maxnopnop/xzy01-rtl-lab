# 初始发现

v1 checker在线FIFO先入后出，理论上可以识别最终序列相同但输出早于输入的因果错误；需真实RTL新见证核验。其reset取消账已有定义，真实中途reset尚未覆盖。旧fsm_ir.py只支持1bit输入/1bit Moore输出、1..32状态，无8bit+last/ready或广播事务表示；本次意图比较不能宣称生产IR已支持此域。

实测early fault最终flat相等，consumer cycle3接受、source cycle7接受，正确拒绝；合法提前valid等待及同拍通过。shared/独立queue reset取消账分别pending[0,1]/unaccepted2和pending[0,2]/unaccepted1，合法结构接受集合不同，事务意图比较需把reset对齐缺口标不可评估。

保留新负结果：shared reset残留最早在新输入接受前出现，实际UNEXPECTED而非预声明DATA_OR_ORDER。无漏检，不为改错误类别重试；完整期望15/16而非全PASS。默认回归仍旧exit1，不宣称仓库测试全PASS；无自然模型效用证据。
