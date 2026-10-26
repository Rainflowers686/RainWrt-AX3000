<div align="center">

# **RainWrt-AX3000**

为 Redmi AX3000 / Xiaomi CR880X 路由器维护的 ImmortalWrt 下游版本。

跟进上游版本，维护设备支持与 NAND 升级路径，并记录 CR8808 的实际硬件验证结果。

![ImmortalWrt](https://img.shields.io/badge/ImmortalWrt-downstream-2B579A)
![CR880X](https://img.shields.io/badge/Hardware-CR880X-6A737D)
[![Source license](https://img.shields.io/badge/License-GPL--2.0%20%2B%20component%20terms-blue)](COPYING)

[English](README.md) · [简体中文](README.zh-CN.md)

[当前状态](#当前状态) · [硬件](#支持的硬件) · [升级安全](#安装与升级安全) · [构建](#构建) · [参与贡献](CONTRIBUTING.md)

</div>

## 当前状态

当前开发版基于 ImmortalWrt 25.12.2、Linux 6.12.103，目标为 `qualcommax/ipq50xx`，设备配置为 `redmi_ax3000`。经清理的公开源码使用本地 board-data 完成干净构建，并于 2026-09-23 在一台 Xiaomi CR8808 / Redmi AX3000 M81 上完成硬件验证。

其他 CR880X 型号、引导程序或分区布局的兼容性尚未验证，当前版本也未达到长线稳定版定位。具体范围见[硬件验证记录](docs/HARDWARE_VALIDATION.md)。

当前公开源码不含设备专属 board-data 二进制。相关再分发许可尚未确认，因此仓库不提供预编译固件。若要自行构建，必须按[board-data 说明](docs/BOARD_DATA.md)在本机准备对应文件；干净检出在缺少这些输入时会停止。

## 维护方向

RainWrt 在 kmiit 24.10 分支停止维护后继续支持 Redmi AX3000 / CR880X。kmiit 构建保留为已知可用的硬件参考；当前代码跟随 ImmortalWrt stable，只保留仍有必要的设备、兼容性和升级安全改动。

## 支持的硬件

| 设备 | 构建配置 | 升级验证 | 硬件状态 |
|---|---|---|---|
| Xiaomi CR8808 / Redmi AX3000 M81 | redmi_ax3000 | 一台设备通过精确匹配的合并 rootfs 单槽 NAND sysupgrade | 以太网、2.4 GHz 和 5 GHz 已验证 |
| Xiaomi CR880X M79 V1 | 仅作构建/参考配置 | 未授权或验证硬件 sysupgrade | 未验证 |
| 其他 CR880X 型号 | 不作兼容声明 | 未验证 | 未验证 |

已测试的 M81 使用定制 Web-Recovery 引导程序，运行时采用合并 rootfs 布局。产品名称或目标平台相同，不足以证明其他设备可以升级。

## 软件栈

- ImmortalWrt 25.12.2
- Linux 6.12.103
- qualcommax/ipq50xx，设备配置 redmi_ax3000
- ath11k；IPQ5018 提供 2.4 GHz，外接 QCN6122 提供 5 GHz
- APK 包管理器与同版本签名索引
- LuCI、中文 LuCI、HTTPS 管理与 WireGuard 支持

这些组件和功能的版本、验证边界请以仓库中的对应记录为准。


## 硬件验证

在已测试的 CR8808 M81 上，NAND sysupgrade、首次启动、一次正常重启、合并运行时 rootfs、UBI 卷、以太网、IPv4/IPv6、两路无线电、ath11k、WireGuard 能力、APK，以及从 24.10 到 25.12 的配置迁移均通过验证。

迁移时必须调整 QCN6122 的无线设备路径；该修改在重启后仍然有效。完整记录见[验证矩阵](docs/HARDWARE_VALIDATION.md)和[hwtest1 审计](docs/HWTEST1_AUDIT.md)。

## 性能

本机 WSL 到路由器的 TCP 测试结果约为：

| 并发流 | 主机到路由器 | 路由器到主机 |
|---|---:|---:|
| 1 | 635 Mbps | 501 Mbps |
| 4 | 748 Mbps | 617 Mbps |
| 8 | 736 Mbps | 642 Mbps |

当时没有可控的 Wi-Fi 转发端点，外部 WireGuard 路径也未受控。因此这些数据不代表 NAT、Wi-Fi 或 WireGuard 的设备吞吐上限。A/B 结果、资源限制及后续有界 10 分钟回归见[性能记录](docs/PERFORMANCE.md)。

<a id="构建与升级"></a>

## 安装与升级安全

24.10 到 25.12 的迁移会改变 QCN6122 无线设备路径。已测试的迁移仅更新精确匹配的旧路径，保留用户其他无线配置。升级代码只接受已识别的布局，拒绝未知状态；对不匹配的硬件或布局不要刷写。开始前请阅读[升级安全说明](docs/UPGRADE_SAFETY.md)。

运行中系统的 NAND sysupgrade 与 Web Recovery factory 恢复是不同路径。CR8808 的恢复监听入口已验证，但 25.12 factory 镜像的恢复写入和启动尚未验证。具体见[恢复限制](docs/RECOVERY.md)和[发布审计](docs/PUBLIC_RELEASE_AUDIT.md)。

## 构建

请在 Linux 大小写敏感文件系统上构建：

~~~sh
JOBS=8 sh scripts/build-rainwrt.sh
python3 tests/test_hardware_runner.py
sh tests/mi_layout_test.sh
sh tests/mi_dualboot_test.sh
~~~

构建脚本固定上游与 feed 版本，并写出构建身份。镜像及其匹配的 APK 索引和包应一起保留，不要混用其他版本的内核包。具体见[构建身份记录](docs/BUILD_IDENTITY.md)。

CR8808 构建需要两个在本机取得的 board-data 文件。构建包装脚本在联网或构建前检查它们的精确 SHA256，随后只将其注入被 Git 忽略的本地包暂存目录。再分发许可尚未确认，仓库不提供这些二进制；详见 [docs/BOARD_DATA.md](docs/BOARD_DATA.md)。

GitHub Actions 运行源码隐私检查与测试，不构建或发布固件。

## WireGuard

内核模块、工具和 LuCI 协议支持已包含，并在实机上验证了能力。公开镜像配置不附带 peer、密钥、私有路由、DNS 策略或默认 VPN 策略；安装后在本地配置自己的 peer。

## 上游与致谢

- [OpenWrt](https://github.com/openwrt/openwrt)
- [ImmortalWrt](https://github.com/immortalwrt/immortalwrt)
- [kmiit Redmi AX3000 ImmortalWrt](https://github.com/kmiit/Redmi_AX3000_immortalwrt)
- [hzyitc OpenWrt Redmi AX3000](https://github.com/hzyitc/openwrt-redmi-ax3000)
- [ByteArray0 ImmortalWrt device expansion](https://github.com/ByteArray0/immortalwrt-device-expand)

## 隐私与许可

公开源码和固件配置不包含私有 Wi-Fi、校园、VPN 或部署信息。保留用户配置属于通用升级行为，不代表对某个私有服务的支持。固件修改仍可能失败；请保留独立验证过的恢复镜像，不要升级布局不匹配的设备。本软件不提供担保。

各组件沿用其原有许可与声明，见 [COPYING](COPYING)、[LICENSES/](LICENSES/)及包元数据。厂商固件和 board-data 有单独条款，不因进入构建流程而改为 GPL；两个 CR8808 专用 board-data 容器的再分发许可仍未确认，详见[发布审计](docs/PUBLIC_RELEASE_AUDIT.md)。

阅读[架构说明](docs/ARCHITECTURE.md)、[构建身份记录](docs/BUILD_IDENTITY.md)、[kmiit 设备差异](docs/KMIIT_DEVICE_DELTA.md)和[前移研究记录](docs/FORWARD_PORT_RESEARCH.md)，了解下游改动及其来源。

## 参与贡献与安全报告

[CONTRIBUTING.md](CONTRIBUTING.md)列出了源码检查和新增硬件支持所需的验证材料。敏感问题按 [SECURITY.md](SECURITY.md)报告，不公开 board-data、私人路由器配置或凭据。
