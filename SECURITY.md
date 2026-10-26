# Security and device safety

RainWrt is a hardware-validated development line with a limited set of tested devices and layouts. Read [UPGRADE_SAFETY.md](docs/UPGRADE_SAFETY.md), [RECOVERY.md](docs/RECOVERY.md) and the [hardware validation record](docs/HARDWARE_VALIDATION.md) before using an image. A passed source check is not authorization to flash an untested device.

Do not publish Wi-Fi passwords, VPN keys, private routes, device identifiers, full configuration backups or local board-data binaries in an issue. Redact logs before sharing them.

## Reporting

If the repository's Security tab offers private vulnerability reporting, use it for exploitable flaws and disclosure risks. Otherwise open an issue asking for a private reporting channel, without exploit details or sensitive attachments. No fixed response deadline is promised.

Include the affected commit, device and layout, the observed behavior, and a reproduction that avoids private data. For inherited components, identify the upstream component and version so the report can be routed appropriately.

## 中文说明

本项目的硬件验证仅覆盖记录中的设备与布局。运行源码检查不能替代刷写前的设备核对；恢复路径的限制见上述文档。

安全问题优先通过仓库已启用的私密漏洞报告入口提交。若没有该入口，先开一条仅询问私下联系渠道的 issue，不附漏洞细节、密钥、配置备份或 board-data。报告说明受影响的提交、设备布局和实际现象，上传前清除私人数据。
