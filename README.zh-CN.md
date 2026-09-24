# RainWrt-AX3000

*为 Redmi AX3000 / Xiaomi CR880X 维护的 ImmortalWrt 下游版本。*

![ImmortalWrt](https://img.shields.io/badge/ImmortalWrt-downstream-2B579A) ![OpenWrt](https://img.shields.io/badge/OpenWrt-router-00A3E0) ![CR880X](https://img.shields.io/badge/Hardware-CR880X-6A737D)



**导航：**[当前状态](#当前状态) · [支持的硬件](#支持的硬件) · [升级安全](#安装与升级安全) · [构建](#构建)

[English](README.md) | [简体中文](README.zh-CN.md)

RainWrt 是基于 ImmortalWrt 维护的下游版本，继续支持 Redmi AX3000 / Xiaomi CR880X。项目重点是跟进上游版本、谨慎处理 NAND 升级，并把设备支持保持在可维护范围内。

## 当前状态

仓库记录的硬件验证针对一台 Xiaomi CR8808 / Redmi AX3000 M81。验证范围和测试日期见[硬件验证记录](docs/HARDWARE_VALIDATION.md)。这不代表所有 CR880X 型号、引导程序或分区布局都兼容，也不构成长线稳定版声明。

当前公开源码不含设备专属 board-data 二进制。相关再分发许可尚未确认，因此仓库不提供预编译固件。若要自行构建，必须按[board-data 说明](docs/BOARD_DATA.md)在本机准备对应文件；干净检出在缺少这些输入时会停止。

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
- ath11k、APK 包管理器、LuCI 与 WireGuard 支持

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

## 构建与升级

请在 Linux 大小写敏感文件系统上构建：

~~~sh
JOBS=8 sh scripts/build-rainwrt.sh
python3 tests/test_hardware_runner.py
sh tests/mi_layout_test.sh
sh tests/mi_dualboot_test.sh
~~~

NAND sysupgrade 与 Web Recovery 恢复是不同路径。升级代码只接受已识别的布局；未知设备状态会被拒绝。对不匹配的硬件或布局不要刷写。开始前请阅读[升级安全说明](docs/UPGRADE_SAFETY.md)、[恢复限制](docs/RECOVERY.md)和[发布审计](docs/PUBLIC_RELEASE_AUDIT.md)。

GitHub Actions 运行源码隐私检查与测试，不构建或发布固件。


## 上游与致谢

- [OpenWrt](https://github.com/openwrt/openwrt)
- [ImmortalWrt](https://github.com/immortalwrt/immortalwrt)
- [kmiit Redmi AX3000 ImmortalWrt](https://github.com/kmiit/Redmi_AX3000_immortalwrt)
- [hzyitc OpenWrt Redmi AX3000](https://github.com/hzyitc/openwrt-redmi-ax3000)
- [ByteArray0 ImmortalWrt device expansion](https://github.com/ByteArray0/immortalwrt-device-expand)

## 隐私与许可

公开源码不包含私有 Wi-Fi、校园、VPN 或部署配置。WireGuard 组件的存在不代表仓库附带 peer、密钥或私有路由。各组件沿用其原有许可与声明；厂商固件和 board-data 有单独条款，详见 COPYING、LICENSES/ 及发布审计。

阅读[架构说明](docs/ARCHITECTURE.md)、[构建身份记录](docs/BUILD_IDENTITY.md)和各项验证文档，了解下游改动及其证据。
