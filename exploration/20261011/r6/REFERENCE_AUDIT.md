# R6 参考依赖与手推见证

全部任务为本机原创开发规格，无引入公开基准/外部原始规格或许可适配；不声称文献新颖性。设计前未发送模型候选。作者同时负责文字和参考，存在共同误读风险；总控审核及不同实现路径不是外部独立作者。

依赖图：文字规则→(A过程状态机 tasks.step；B不同抽象 reference_alt；C手写SV)→公开/隐藏事件对照；文字规则→手算公开rising见证→A/B/C校准。端口打包由tasks共享，随机/定向输入由tasks生成；B共享unpack和端口接口但不调用A的step；C不调用Python；IR teacher为人工正确校准，不送真实生成。

| 机制 | A过程参考 | B推导路径 | C实现与共同依赖 |
|---|---|---|---|
| ordered_retire | 有序列表，先取旧队列退休资格，再标记幸存票据，最后按旧容量/旧标签接纳 | 独立单调age字典，min(age)确定头；旧字典校验接纳与标记 | 固定双槽寄存器/组合next。均依赖同一old-state文字及共享打包，未全状态穷尽。 |
| restoring_divide | 四次恢复除法trial/subtract/shift | acceptance时用整数divmod计算目标值，独立剩余advance计数决定可见发布；避免共享逐位算法 | 手写shift/subtract datapath。B不能直接证明不可观察内部partial值，只核可见时机/商余数。 |
| tagged_join | 独立槽状态字典及旧状态捕获/比较/替换优先级 | 两个可选(tag,data)对象；三值比较决定drop/move，独立输出槽 | 显式input holding寄存器与NBA优先级。均同文字，不证明无限流公平性。 |

手算公开轨迹，每次开始异步reset，packed outputs按端口表从高到低：

- ordered：issue1→count1；issue2→count2；finish2仍count2；finish1仍count2（当拍不能退休）；下一拍OLD头已ready，满OLD队列拒issue3，退休1/count1；再退休2/count0；下一拍retired清0、tag2保持。packed rising为 **8,16,16,16,13,6,2**。
- divide：接受13/3只开始，不advance；advance1、pause、advance2、advance3均busy=1且旧输出0；advance4同时start8/2被忽略，13 div 3商4余1，busy0/done1；下一拍done0、商余保持。packed为 **512,512,512,512,512,321,65**。13的二进制1101按四次trial为1、3、0、1，对3产生quotient0100/remainder1。
- join：A(tag1,data2)先占A；B(tag1,data3)占B；下一拍配对发布(tag1,data11)；再接A0/data1、B2/data2，旧output占用；下一拍不等丢A；再接A2/data1；相等但output blocked保持；take时配对替换，输出tag2,data6。packed为 **256,384,91,475,219,475,475,102**。

calibration-v1检查这些手算值，并将A/B及人工teacher IR在相同完整固定事件集比较；三SV各跑public/private共6次真实Icarus；三个目标故障各private一次，总9compile/9sim。人工错误是当拍finish即退休、除法少一次advance、join反转小tag丢弃。仅确认针对性检出，不代表广泛故障覆盖或模型收益。

限制：三参考依赖同文字，打包共源；手算只少量公开路径；短随机和定向固定轨迹不等于独立最终集或无界证明。隐藏刺激/期望与源码不送模型；本轮调优/参考检查过的任务都标development。
