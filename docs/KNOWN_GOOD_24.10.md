# Known-good 24.10 reference

Hardware validation: 2026-09-22. Reference: `legacy/kmiit-24.10` and annotated
tag `known-good/cr8808-2026-09-22`.

- kmiit base: `9a11bb83d22efd5879439427cd222b957f6f7019`
- built source: `2b3c09192733671d597df8287f4d788047dadccf`
- ImmortalWrt 24.10-SNAPSHOT, Linux 6.6.137
- sysupgrade SHA256: `bd552ead7a42f1355195c9dc72eb7bcf798886f4886fba86d5c29d3aa0e7e7d1`
- recovery factory SHA256: `7b48d723d93612c6fb8857ec4f05ac7faf62242f6848e5686f53fc8ff6752e69`

Verified: boot, merged-rootfs NAND sysupgrade, UBI reconstruction, second
reboot, LAN/WAN, IPv4/IPv6, IPQ5018 2.4 GHz, QCN6122 5 GHz, ath11k,
WireGuard module/tools/LuCI and Web-Recovery entry. No other variant is implied.
