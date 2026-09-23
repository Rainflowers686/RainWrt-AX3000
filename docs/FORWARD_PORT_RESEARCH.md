# Forward-port research

Research checked 2026-09-22 selected ImmortalWrt 25.12.2 as the maintained
stable base. Its official qualcommax/ipq50xx tree did not list a Redmi AX3000 /
CR880X device profile. OpenWrt 25.12.5 was reference-only and likewise had no
matching profile. kmiit 24.10 is the functional reference. ByteArray0's
ImmortalWrt 25.12 port supplied the modern Linux 6.12 DTS/API starting point.

The third-party port was not accepted blindly: it hardcodes a Web-Recovery
merged rootfs and changes the M81 identity. RainWrt restores the verified
redmi_ax3000 identity, rejects unknown layouts and disables M79 sysupgrade
until independently verified. NSS, overclocking and private runtime
configuration remain outside the public feature set.

Official download-index recheck on 2026-09-22 found no matching device profile
in ImmortalWrt 25.12.2 stable or snapshot, or OpenWrt 25.12.5 stable or
snapshot. The check compared device names and metadata; it did not infer
support from the existence of the qualcommax subtarget.

- ImmortalWrt stable:
  https://downloads.immortalwrt.org/releases/25.12.2/targets/qualcommax/ipq50xx/profiles.json
- ImmortalWrt snapshot:
  https://downloads.immortalwrt.org/snapshots/targets/qualcommax/ipq50xx/profiles.json
- OpenWrt stable:
  https://downloads.openwrt.org/releases/25.12.5/targets/qualcommax/ipq50xx/profiles.json
- OpenWrt snapshot:
  https://downloads.openwrt.org/snapshots/targets/qualcommax/ipq50xx/profiles.json

The hwtest1 re-audit corrected board-case propagation, BDF override consumer
removal, changed memory budgets and a missing conditional qfprom fix. The
resulting build passed scoped hardware validation on one CR8808 M81; this does
not validate other variants. See KMIIT_DEVICE_DELTA.md and
HARDWARE_VALIDATION.md.

The exact CR8808-specific board-data containers are not present in the
inspected upstream BDF repository. Their vendor-origin redistribution grant is
unresolved, so this source repository must remain private pending licensing
clearance. See PUBLIC_RELEASE_AUDIT.md.
