# Hardware validation — CR8808 M81

## Current public-source tested build

- Device: one Xiaomi CR8808 / Redmi AX3000 M81
- Runtime identity: RainWrt 25.12.2-hwtest1
- Base: ImmortalWrt 25.12.2, upstream revision
  `4fc16f2985a358bd43bb522e43f05395fcbd6ed5`
- Kernel: Linux 6.12.103
- Target/profile: `qualcommax/ipq50xx` / `redmi_ax3000`
- Firmware source revision: `21c77ebdeeb8e04b5192e100b074a8edaf6f32d3`
- Sysupgrade image: 18,585,872 bytes; SHA256
  `a2de8fe525b3d217c0c2c4fea0757e74c84c0a34c603292b9594f6ed1eb46441`
- Factory UBI: 19,529,728 bytes; SHA256
  `9592802d6b3bf842a9815b923c16a00203cfac02f9ffb3eebd727c6cf75bfd46`
- Initramfs ITB: 18,487,084 bytes; SHA256
  `ada091c6df6a7620384e7296943f11148151a79121db4794543d90aab0d6f622`
- Board data was supplied locally, not from the public repository. The exact
  hashes and board IDs are documented in [BOARD_DATA.md](BOARD_DATA.md).

The source was clean-built, statically audited, accepted by `sysupgrade -T`,
installed using standard NAND sysupgrade, and passed first-boot plus one normal
reboot validation. The public source does not contain or redistribute the
board-data files. This validates one tested unit only; it does not authorize a
binary release or generalize to other CR880X devices.

## Historical initial 25.12 validation

The earlier hwtest1 image was built from source revision
`ff21ae557201e2def1ca4770275abca2fdae477f`; its tested sysupgrade SHA256 was
`98099b26672fdb0931a30673792402f42194dbac66a559520596d4b86e58121c`. This
historical source revision is distinct from the current sanitized
public-source build. The old restricted-BDF tree is not reachable from public
refs. The earlier public-safe provenance tag remains distinct from the new
hardware-validation tag.

## Result matrix

| Area | Result | Evidence boundary |
|---|---|---|
| NAND sysupgrade | PASS | Standard sysupgrade completed on the tested merged-rootfs device |
| Clean public-source build | PASS | Source revision above built from clean package/image outputs with local-only board data |
| Static artifact audit | PASS | Metadata, image structure, package manifest and matching build identity checked |
| First boot | PASS | Exact RainWrt build identity and kernel verified |
| Normal reboot | PASS | Second boot returned and passed the scoped validation |
| Runtime partition map | PASS | Single runtime mtd18=rootfs geometry and UBI layout matched the tested M81 |
| UBI | PASS | kernel, rootfs and rootfs_data volumes were present and mounted as expected |
| Ethernet | PASS | LAN/WAN and expected links operated |
| IPv4 / IPv6 | PASS | Both stacks worked after install and reboot |
| IPQ5018 2.4 GHz | PASS | ath11k active; XPA board ID 0x10 |
| QCN6122 5 GHz | PASS | ath11k active; board ID 0x60 |
| Wireless migration | PASS | Exact 24.10 QCN6122 path migrated to the 25.12 path; two radios worked and the change persisted across reboot |
| WireGuard capability | PASS | Kernel module, tools and LuCI protocol were present and functional as packages; no private peer is part of this result |
| APK | PASS | Release-matched signed package indexes and package operations were verified |
| Configuration migration | PASS | 24.10 user configuration migrated through the reviewed opaque-preservation path |
| Custom service state | PASS | The generic preserved-service enable/disable migration path passed |
| Private runtime preservation | PASS | Current private snapshot comparison was 22 same, 0 different, 0 missing; sysupgrade backup/list checks passed |
| WG/WAN fallback | PASS | A bounded interface-down test moved IPv4 to WAN, preserved WAN6, then the health manager restored WG and the WG IPv4 route |
| Bounded stability regression | PASS | Ten minutes of bidirectional local TCP load completed; no OOM, ath11k fatal or remoteproc error was observed |

The wireless migration changes only the exact known old QCN6122 device path in
the configuration archive. The user's other wireless settings are preserved
byte-for-byte.

## Layout and recovery boundary

The tested device's MIBIB retains the stock dual-slot table, while its custom
Web-Recovery APPSBL supplies a runtime FDT fixup exposing one merged rootfs
partition. See CR8808_FLASH_LAYOUT.md. This finding is specific to the
fingerprinted unit; it is not a universal CR880X layout claim.

Reset plus power-on reached the CR8808 Web-Recovery listener at 192.168.10.1.
That listener test did not upload firmware. A full write and boot of a 25.12
factory image through Web Recovery has not been hardware validated.

## Known limits

- Evidence covers one CR8808 M81 only.
- M79 V1, stock dual-slot installations and other CR880X variants are not
  authorized or hardware validated for sysupgrade.
- No controlled Wi-Fi forwarding endpoint was available.
- No controlled WireGuard iperf endpoint was available.
- No 25.12 factory-image write/boot through Web Recovery has been tested.
- The external WireGuard measurements are path experience, not device limits.
- Multi-week stability and a 25.12 factory Web-Recovery restore remain untested.
- A successful hash or static image audit is not a substitute for device testing.

See HWTEST1_AUDIT.md, UPGRADE_SAFETY.md and RECOVERY.md before considering any
upgrade.
