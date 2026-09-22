# RainWrt-AX3000

A public, auditable device downstream of **ImmortalWrt stable**, retaining
Redmi AX3000 / Xiaomi CR8808 support after kmiit's 24.10 reference line.

## Status and hardware boundary

The 24.10 / Linux 6.6.137 reference is hardware-verified. The 25.12.2 /
Linux 6.12.103 line is a **hardware-test candidate**, not a stable release.
hwtest1 passed first-boot and one normal-reboot validation on the fingerprinted
CR8808 after correcting the preserved QCN6122 wireless path. See the
[hwtest1 checkpoint](docs/HWTEST1_AUDIT.md) for the exact evidence and limits.
It targets IPQ5018 + QCN6122, M81/CR8808 with the explicitly fingerprinted
Web-Recovery bootloader and merged NAND layout. Other CR880X variants,
stock dual-slot layouts and unknown bootloaders are not authorized to upgrade.
M79 writes are disabled.

Normal upgrades do not require UART. Recovery is manual through the previously
verified bootloader web page. A reachable recovery listener does not prove that
every uploaded image can recover every failure. Read [recovery](docs/RECOVERY.md)
and [upgrade safety](docs/UPGRADE_SAFETY.md) first. No warranty is provided.

## Build and test

Use a native Linux case-sensitive filesystem, not a Windows-mounted source
directory. Install the normal ImmortalWrt build dependencies, Python 3 and
ShellCheck; build as an unprivileged user from a clean checkout:

```sh
JOBS=8 sh scripts/build-rainwrt.sh
python3 tests/test_hardware_runner.py
sh tests/mi_layout_test.sh
sh tests/mi_dualboot_test.sh
```

Feeds are commit-pinned. The build generates an ignored runtime identity from
clean source HEAD; see [build identity](docs/BUILD_IDENTITY.md). Retain all
matching signed APK indexes and packages with the images. Do not mix official
core packages into the downstream kernel. No hosted downstream repository is
configured for this experimental candidate.

The attended hardware runner defaults to dry-run and never retries a write.
Read [the hardware test plan](docs/HARDWARE_TEST_25_12.md); a local reviewed
candidate manifest is mandatory. Do not use the legacy 24.10 installer for
the 25.12 transition.

## Public feature boundary

LuCI, Chinese LuCI, HTTPS administration, WireGuard, wpad-openssl and lightweight
diagnostics are included. WireGuard has no default interface, key, endpoint or
private route. User configuration is opaque private data, not a public feature.
No institutional authentication, proxy suite, Docker, aggressive NSS offload,
overclock or private DNS is included.

## Upstream and attribution

- [OpenWrt](https://github.com/openwrt/openwrt)
- [ImmortalWrt](https://github.com/immortalwrt/immortalwrt)
- [kmiit device reference](https://github.com/kmiit/Redmi_AX3000_immortalwrt)
- [hzyitc original device work](https://github.com/hzyitc/openwrt-redmi-ax3000)
- [ByteArray0 6.12 port](https://github.com/ByteArray0/immortalwrt-device-expand)

Inherited authorship is retained. RainWrt changes are separately committed.
Source licensing remains in [LICENSE](LICENSE); individual packages and vendor
firmware have their own terms. Vendor binaries are not relicensed as GPL.
See [device delta](docs/KMIIT_DEVICE_DELTA.md), [architecture](docs/ARCHITECTURE.md),
[performance](docs/PERFORMANCE.md), and [public release audit](docs/PUBLIC_RELEASE_AUDIT.md).
