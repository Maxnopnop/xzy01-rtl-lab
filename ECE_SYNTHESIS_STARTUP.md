# ECE 桌面综合工具启动记录

验证日期：2026-10-09。环境：通过学校 VPN 和 Omnissa Horizon 进入 ECE Linux 桌面，验证主机为 `ecelvd703`，操作系统为 CentOS 7.9。

## 验证结果

| 工具 | 验证版本 | 环境脚本 | 已确认情况 |
| --- | --- | --- | --- |
| Synopsys Design Compiler | X-2025.06-SP2 | `/usr/eelocal/synopsys/syn-vx2025.06-sp2/.cshrc` | 成功进入 `dc_shell>`，正常退出，提供的启动输出没有许可证失败信息 |
| Cadence Genus | 21.14-s082_1 | `/usr/eelocal/cadence/genus211/.cshrc` | 成功进入 Genus 命令行，明确取得 `Genus_Synthesis` 许可证，正常退出 |

记录依据为用户提供的实际学校终端截图和输出。这些结果属于启动验证，尚未执行 RTL 综合；DC 的具体综合功能许可证仍需通过实际综合确认。

## 启动 Design Compiler

在学校 Linux 终端逐行执行以下命令。使用独立的 tcsh 子 shell 加载 `.cshrc`，避免依赖当前终端的 shell 类型，也避免与其他工具的配置混用。

```tcsh
tcsh -f
source /usr/eelocal/synopsys/syn-vx2025.06-sp2/.cshrc
dc_shell
```

出现 `dc_shell>` 表示已进入工具。在该提示符下输入：

```tcl
exit
```

工具退出后，在 Linux 子 shell 中再输入一次：

```tcsh
exit
```

实际验证中，DC 从已有的 tcsh 终端直接加载环境后启动成功。上面的独立子 shell 写法用于后续重复操作。

已发现的可执行文件：

```text
/usr/eelocal/synopsys/syn-vx2025.06-sp2/bin/dc_shell
/usr/eelocal/synopsys/syn-vx2025.06-sp2/linux64/syn/bin/dc_shell
```

## 启动 Genus

在学校 Linux 终端逐行执行：

```tcsh
tcsh -f
source /usr/eelocal/cadence/genus211/.cshrc
genus
```

实际输出包含以下信息：

```text
Version: 21.14-s082_1
Periodic Lic check successful
Checking out license: Genus_Synthesis
```

进入的命令提示符为 `@genus:root: 1>`。在 Genus 中输入：

```tcl
exit
```

输出 `Normal exit.` 后，在 Linux 子 shell 中再输入一次：

```tcsh
exit
```

启动时出现版本较旧的警告，但本次仍成功取得许可证并进入命令行。

已发现的可执行文件包括：

```text
/usr/eelocal/cadence/genus211/bin/genus
/usr/eelocal/cadence/genus211/tools.lnx86/bin/genus
/usr/eelocal/cadence/genus211/tools.lnx86/synth/bin/genus
```

## 与现有实验的关系

- 本机已有的“综合通过”结果来自 Yosys。
- 学校 VCS 和 Xcelium 的已验证结果属于 RTL 仿真。
- 本次 DC 和 Genus 只完成启动检查，不能计为“综合通过”，也没有产生综合网表、面积或时序结果。
- 后续实际综合应绑定原始 RTL 和实验结果的哈希，保存脚本、工具版本、约束、库配置和日志，不覆盖原始模型输出。

## 后续需要确认的资源

向导师或 `eehelp@ece.ust.hk` 确认：

1. FYP 可使用的数字标准单元库及访问权限。
2. DC 使用的 `.db` 和 Genus 使用的 Liberty `.lib` 路径，以及推荐工艺角。
3. 推荐的时钟、输入输出时序约束和示例综合脚本。
4. 学校桌面上手动运行单个综合任务的使用要求。

标准单元库与约束确认后，再用一个已有 RTL 样本验证读取、展开、综合、导出网表和生成面积/时序报告。报告的含义取决于所使用的库、工艺角和约束；综合成功不等于功能正确。

现有共享 VDI 不支持 SSH、EDA 批量任务或 EDA 调度器。保持在已登录主机上手动运行单个任务的方式，直到学校明确允许其他方式。

## 课程资料访问问题

此前 `/staff/ee/dept/public/elec5550/ELEC5550_Lab.zip` 访问失败。`elec5550` 指向 `elec6910d`，目录权限为 `drwxrws---`，当前账号访问受阻。这属于课程资料权限问题，不能据此判断综合工具许可证不可用；也不能在无法访问父目录时断定压缩包不存在。

## 工具说明

[Cadence 官方 Genus 产品说明](https://www.cadence.com/en_US/home/tools/digital-design-and-signoff/synthesis/genus-synthesis-solution.html)介绍了 Genus 的 RTL 逻辑综合与物理综合用途。学校安装版本和本账号启动结果以本记录中的实际终端证据为准。
