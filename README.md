# RainWrt-AX3000

A maintained ImmortalWrt downstream for Redmi AX3000 / Xiaomi CR880X, focused
on current kernels, careful NAND upgrade handling and maintainable device
support.

## Status

**Hardware-validated development release:** ImmortalWrt 25.12.2, Linux
6.12.103, target `qualcommax/ipq50xx`, profile `redmi_ax3000`.

Hardware validation is based on one Xiaomi CR8808 / Redmi AX3000 M81. This is
not a claim that every CR880X variant or bootloader is compatible, and RainWrt
does not yet claim a long-term stable release. See
[hardware validation](docs/HARDWARE_VALIDATION.md).

Public release is blocked while redistribution rights for the device-specific
wireless board data are unresolved. Any GitHub repository containing this
source must remain private until that question is resolved. No binary GitHub
Release is published.

## Why RainWrt

RainWrt continues Redmi AX3000 / CR880X support after the kmiit 24.10 line
stopped being maintained. The kmiit build is preserved as a known-good hardware
reference, not used as the permanent base. The maintained line follows
ImmortalWrt stable and carries only the device, compatibility and upgrade-safety
deltas that remain necessary.

## Supported hardware

| Device | Build/profile | Upgrade validation | Hardware status |
|---|---|---|---|
| Xiaomi CR8808 / Redmi AX3000 M81 | `redmi_ax3000` | Exact merged-rootfs single-slot NAND sysupgrade passed on one unit | Ethernet, 2.4 GHz and 5 GHz validated |
| Xiaomi CR880X M79 V1 | Build/reference profile only | Not authorized or hardware validated for sysupgrade | Not validated |
| Other CR880X variants | No compatibility claim | Not validated | Not validated |

The tested M81 has a custom Web-Recovery bootloader and a runtime merged rootfs
layout. A matching marketing name or target is not enough to authorize an
upgrade on another device.

## Current stack

- Base: ImmortalWrt 25.12.2
- Kernel: Linux 6.12.103
- Target/profile: `qualcommax/ipq50xx` / `redmi_ax3000`
- Wi-Fi: ath11k; IPQ5018 2.4 GHz and external QCN6122 5 GHz
- Package manager: APK, using release-matched signed indexes
- User features: LuCI, Chinese LuCI, HTTPS administration and WireGuard

## Hardware validation

On the tested CR8808 M81, NAND sysupgrade, first boot, one normal reboot, the
merged runtime rootfs, UBI volumes, Ethernet, IPv4/IPv6, both radios, ath11k,
WireGuard capability, APK and 24.10-to-25.12 configuration migration passed.
The QCN6122 wireless-device path migration was required and persisted across
reboot. See the full [validation matrix](docs/HARDWARE_VALIDATION.md) and
[detailed hwtest1 record](docs/HWTEST1_AUDIT.md).

## Performance

Local WSL-to-router TCP tests reached approximately 635/501 Mbps with one
stream, 748/617 Mbps with four streams and 736/642 Mbps with eight streams
(host-to-router / router-to-host). A controlled Wi-Fi forwarding endpoint was
not available, and the external WireGuard path was not controlled. These are
not NAT, Wi-Fi or WireGuard device-throughput limits. A/B results and resource
limits are in [performance notes](docs/PERFORMANCE.md).

## Installation and upgrade safety

The 24.10-to-25.12 transition changes the QCN6122 wireless path. The tested
migration updates only that exact known old path while preserving the user's
other wireless configuration. Upgrade code is restricted to recognized
fingerprints and rejects unknown layouts. Read
[upgrade safety](docs/UPGRADE_SAFETY.md) before considering an image.

The running-system sysupgrade path and Web Recovery factory path are different.
The CR8808 recovery listener was verified, but a 25.12 factory-image recovery
write and boot have not been validated. See
[recovery limitations](docs/RECOVERY.md).

## Building

Build on a native Linux case-sensitive filesystem:

```sh
JOBS=8 sh scripts/build-rainwrt.sh
python3 tests/test_hardware_runner.py
sh tests/mi_layout_test.sh
sh tests/mi_dualboot_test.sh
```

The build script pins upstream/feed revisions and writes build identity data.
Images and their matching APK indexes/packages must be retained together; do
not mix kernel packages from another release. See
[build identity](docs/BUILD_IDENTITY.md).

## WireGuard

The kernel module, tools and LuCI protocol are included and were hardware
validated as capabilities. The public image contains no peer, key, private
route, DNS policy or default VPN policy. Configure a peer locally after
installation.

## Privacy and recovery warning

RainWrt source and firmware do not include private Wi-Fi, campus, VPN or
deployment configuration. Standard user configuration preservation is generic
and does not imply support for any private service. Firmware changes can still
fail; keep an independently verified recovery image and do not upgrade an
unmatched layout. This software is provided without warranty.

## Upstream and credits

- [OpenWrt](https://github.com/openwrt/openwrt)
- [ImmortalWrt](https://github.com/immortalwrt/immortalwrt)
- [kmiit Redmi AX3000 ImmortalWrt](https://github.com/kmiit/Redmi_AX3000_immortalwrt)
- [hzyitc OpenWrt Redmi AX3000](https://github.com/hzyitc/openwrt-redmi-ax3000)
- [ByteArray0 ImmortalWrt device expansion](https://github.com/ByteArray0/immortalwrt-device-expand)

See [architecture](docs/ARCHITECTURE.md),
[kmiit device delta](docs/KMIIT_DEVICE_DELTA.md) and
[forward-port research](docs/FORWARD_PORT_RESEARCH.md) for provenance and
downstream changes.

## License

The OpenWrt/ImmortalWrt source and inherited components retain their original
licenses and notices; see `COPYING`, `LICENSES/` and individual package
metadata. Vendor firmware and board-data files have separate terms and are not
relicensed as GPL. Redistribution of the two CR8808-specific board-data
containers is not yet cleared; see
[the public-release audit](docs/PUBLIC_RELEASE_AUDIT.md).
