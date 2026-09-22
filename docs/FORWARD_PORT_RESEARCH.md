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
