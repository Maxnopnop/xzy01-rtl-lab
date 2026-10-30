# 核查记录

result先于STOP持久化导致崩溃窗口，已改为gate直接检查所有持久结果。安全继续需要当前schema及显式infrastructure_stop=false，不把字段缺失当false。

原runner回归首次两个loopback测试受环境影响，未收到HTTP请求。urllib检测到http/https代理（环境变量列表无代理，可能来自系统配置）。仅测试进程NO_PROXY=*复验；不修改旧runner/系统配置，保留首次失败日志。

复验仍失败：rtl_lab.clean_env按白名单过滤环境，不传NO_PROXY到API worker。此旧runner问题与r1修改不相交，有限范围内不更改旧模块。完整runner回归未通过，如实留作限制；console63项带网络/子进程审计全部通过。
