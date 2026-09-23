# Hardware validation — CR8808 M81

## Exact tested build

- Device tested: one Xiaomi CR8808 / Redmi AX3000 M81
- Runtime identity: RainWrt 25.12.2-hwtest1
- Base: ImmortalWrt 25.12.2, upstream revision
  4fc16f2985a358bd43bb522e43f05395fcbd6ed5
- Kernel: Linux 6.12.103
- Target/profile: qualcommax/ipq50xx / redmi_ax3000
- Firmware source revision: ff21ae557201e2def1ca4770275abca2fdae477f
- Tested sysupgrade image: 18,585,872 bytes
- SHA256 of the retained exact tested artifact:
  98099b26672fdb0931a30673792402f42194dbac66a559520596d4b86e58121c

The artifact checksum was re-read from the retained hwtest1 build/evidence
copies during project closeout. Later tooling and documentation commits are not
the firmware source revision and do not imply that the firmware was rebuilt.
The original annotated tag pointed to the tested source history, which
contained the board-data inputs. That tag is not part of the sanitized public
refs. The public-safe tag
`validated/cr8808-25.12.2-hwtest1-public-source-2026-09-22` records this
provenance without retaining those blobs: its target is a sanitized source and
documentation commit, not the source commit used for the tested image. The
public source requires users to supply the exact local board-data hashes; the
sanitized commit has not itself been flashed or hardware revalidated.

## Result matrix

| Area | Result | Evidence boundary |
|---|---|---|
| NAND sysupgrade | PASS | Standard sysupgrade completed on the tested merged-rootfs device |
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
- The external WireGuard measurements are path experience, not device limits.
- Multi-week stability and a 25.12 factory Web-Recovery restore remain untested.
- A successful hash or static image audit is not a substitute for device testing.

See HWTEST1_AUDIT.md, UPGRADE_SAFETY.md and RECOVERY.md before considering any
upgrade.
