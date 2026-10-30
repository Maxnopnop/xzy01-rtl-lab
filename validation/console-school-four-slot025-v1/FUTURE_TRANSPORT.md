# 后续控制台传输设计（建议，未实施远程Git）

用户询问后续是否可用Git稳定传输。建议网络/认证允许时使用专用私有Git仓库：控制台导出白名单输入和脚本，固定commit；学校clone/fetch到HOME，本次运行checkout固定commit而非浮动分支；原文件SHA256另行验证，通过后人工启动单工具。运行目录与仓库分离，不在运行中pull，不把代码更新当作重试授权。

git属性必须防止原题、提示、请求、RTL/TB/reference发生自动换行转换（冻结payload按原字节存储）；Git提交ID不能替代已有逐文件SHA256。密钥与学校工艺库不进入仓库；库仅保留学校路径与校验信息。结果保留单独runID、输入commit及文件hash，压缩归档；共享只作为结果归档传输备选，后续网络回传目的地需明确配置。

学校无法访问远程仓库时可使用git bundle：完整或增量Git对象与引用打成一个文件，传到HOME后verify并clone/fetch。bundle不需要活动Git服务端，但仍需要可用的单文件传输渠道；不能向bundle直接push。引用Git官方 https://git-scm.com/docs/git-bundle 与 https://git-scm.com/docs/git-clone 。

Windows本机git 2.53.0.windows.3已确认；学校git版本、仓库网络及权限尚未验证。未创建远程仓库、未push任何文件、未改变本轮学校四工具方案。当前先用同一48文件ZIP解决传输，等待现场验收。
