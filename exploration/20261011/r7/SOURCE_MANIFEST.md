# 来源清单与版权保全

机器清单SOURCE_MANIFEST.json保存所有原字节路径/URL/hash/大小及候选对应原README/source/test/作者/许可。来源访问记录source-access.json包含所有成功/404，原请求不重试，0 HTTP403；fixed commit而非可变master作为RTL与test基线。

axis：[原仓库](https://github.com/alexforencich/verilog-axis/tree/48ff7a7e2ef782cf778d47910cf85835c64b1bce)，Alex Forencich，MIT，COPYING与AUTHORS原样保留。README已标deprecated，不把历史源称当前推荐实现。来源文字与测试/RTL主要同作者，不独立于彼此；独立于本项目作者是不同属性。

cells：[原仓库](https://github.com/pulp-platform/common_cells/tree/e73baaec2ca665cd80c3c384e9258e35242b829c)，ETH Zurich/University of Bologna，源码作者Philippe Sauter/Antonio Pullini/Michael Schaffner；Solderpad Hardware License0.51全文保留。cc_fifo作者Florian Zaruba，仅关联背景，fifo_v3原身份未确认。没有联系作者/上传源/凭据或变更仓库许可。

复用范围为本机来源审计与两个手写TB的原源观测；原copyright/license不移除。生产适配diff为空，参数差异完整见access-adaptation.json；不能把改小参数的观测叫原默认配置全测试。没有原外部文字spec与author-ref之外的独立权威golden，未宣称reference已经无界验证、非LLM辅助或训练未见。
