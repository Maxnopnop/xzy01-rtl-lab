# 从私有 GitHub 传输单例综合包

2026-10-09：用户在 ECE 桌面读取 Horizon 共享 ZIP 超时（退出码124）。本备用路径仅改变传输，复用原始 DC/Genus 单例包及其输入锁，不修改 RTL 或模型实验成绩。

包：`ece_git_packages/xzy01-synth-local-20261009.zip`（26785字节）。外层及内层 ZIP 的 CRC、包哈希和每个冻结输入的 SHA-256 已核对。包内只有 RTL、SDC、脚本和清单，没有标准单元库、商业软件、密钥或许可证文件。

## 浏览器下载

在学校 Linux 桌面的浏览器登录本私有 GitHub 仓库，打开上述 ZIP 并点击 Download raw file，保存到学校 `~/Downloads`。不要在本机 Windows 下载再通过已超时的共享目录传入。无需向 Codex 提供密码或 token。

先校验下载文件的 SHA-256：

```text
13b9b9213082c0e81b0388620fbb92b793a274ceb4319be9f9e84de5113f453a
```

在学校家目录新建独立目录，使用 `python3 -m zipfile -e ZIP文件 新目录` 解压。进入新目录后，手动运行 `bash start_local_dc.sh`。DC 结果核对后，才另外运行 `bash start_local_genus.sh`。两个启动器各自只选择一个案例，不批量调度。

结果保存在解压目录 `returned/`，完整执行目录位于 `~/xzy01-synthesis/session-*`。本路径不会访问 Horizon 进行回传。学校执行后可通过学校浏览器上传回传 ZIP 和配套 JSON 至私有仓库的独立结果位置；请勿把库文件或工具安装目录上传。

## 实验边界

Liberty典型角由用户终端输出确认：1.10V、25°C，ns、fF。`.db`内容及真实工具加载仍需学校日志验证。10ns时钟和I/O约束为首次流程测试假设；异步复位路径被排除，未覆盖复位释放时序，不是签核。

传输就绪不等于综合成功。DC/Genus真实结果待学校手动执行及回传审阅。
