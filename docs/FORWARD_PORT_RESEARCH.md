# Forward-port research

Checked 2026-09-22: ImmortalWrt v25.12.2 is the selected stable base. Its
official `qualcommax/ipq50xx` tree has no Redmi AX3000/CR880X profile. OpenWrt
25.12.5 is reference-only and likewise has no matching profile. kmiit 24.10 is
the functional reference. ByteArray0 `immortalwrt-25.12` supplies a current
CR880X Linux 6.12 port.

That third-party port was not accepted blindly: it hardcodes the Web-Recovery
merged `0x07480000` rootfs and renamed M81. RainWrt restores the verified
`redmi,ax3000` identity, rejects unknown layouts and disables M79 sysupgrade
until proven. NSS, overclocking, proxy stacks and private configuration remain
out of scope.

Independent download-index recheck (2026-09-22): stable ImmortalWrt 25.12.2
listed 14 profiles; its snapshot 17; OpenWrt 25.12.5 listed 13; its snapshot
17. None matched redmi_ax3000, redmi,ax3000, CR8808 or CR880X in names/metadata.
Sources: each project's official `targets/qualcommax/ipq50xx/profiles.json`
under the selected release and snapshot. This is device-level evidence, not
an inference from the existence of the subtarget.

- [ImmortalWrt stable index](https://downloads.immortalwrt.org/releases/25.12.2/targets/qualcommax/ipq50xx/profiles.json)
- [ImmortalWrt snapshot index](https://downloads.immortalwrt.org/snapshots/targets/qualcommax/ipq50xx/profiles.json)
- [OpenWrt stable index](https://downloads.openwrt.org/releases/25.12.5/targets/qualcommax/ipq50xx/profiles.json)
- [OpenWrt snapshot index](https://downloads.openwrt.org/snapshots/targets/qualcommax/ipq50xx/profiles.json)

The hwtest1 re-audit found incomplete board-case propagation, BDF override
consumer removal, changed memory budgets and the missing conditional qfprom
fix. See KMIIT_DEVICE_DELTA.md; the earlier candidate's successful compilation
did not establish hardware correctness. New 6.12 remoteproc/DSA integration
still requires attended testing even after those static defects are repaired.
