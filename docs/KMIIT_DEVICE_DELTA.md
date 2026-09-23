# kmiit device delta

Reference: kmiit/Redmi_AX3000_immortalwrt, base
9a11bb83d22efd5879439427cd222b957f6f7019.

| Area | Disposition | Notes |
|---|---|---|
| Target/image | Forward-ported | Modern IPQ5018 DTS/UbiFit; redmi,ax3000 retained for M81. |
| IPQ5018/QCN6122 remoteproc and memory | Newer API | Based on the maintained 6.12 DTS and passed scoped M81 validation. |
| QCA8337 dual CPU links | Required | 6.12 DSA fixes retained with authorship and passed Ethernet validation. |
| PHY DAC/PHY-to-PHY | Newer API | Expressed by 6.12 DTS and DSA patches; tested on one M81. |
| PA-dependent IPQ5018 board ID | Required | EPA 0x24; XPA/IPA/default 0x10. XPA 0x10 passed on the tested unit. |
| QCN6122 board data | Required | Board package/caldata path retained; board ID 0x60 passed on the tested unit. |
| QCN6122 wireless UCI path | Forward-port | Exact 24.10 path is migrated to the 25.12 DTS path. Both radios and reboot persistence passed on one M81. |
| ath11k smallbuffers | Rewritten | Restore known-good ring limits with a CR8808-only boolean, not a recursive package variant. Memory mode 2 keeps 4 vdevs / 32 peers. |
| RSSI workaround | Already in port | Patch 947 handles IPQ5018/QCN6122 station RSSI. No duplicate patch. |
| Dual-slot upgrade | Disabled | Current DTS fixes a merged layout; stock writes need a separately verified profile. |
| Big-rootfs upgrade | Rewritten | Full MTD/MIBIB/APPSBL/bootcmd fingerprint, fail-closed. |
| M79 V1 upgrade | Disabled | Requires an independent layout fingerprint and hardware validation. |

Imported commits preserve original authorship; RainWrt safety changes are
separate commits.

## Independent re-audit and hardware result

The hwtest1 re-audit corrected board-case propagation, caldata for both radios,
Ethernet and LED cases, environment-reader identity, the active APPSBL index,
the ath11k DT/filesystem board override consumer and conditional qfprom byte
reads. Ethernet aliases preserve the reference eth0/eth1 order. No write path
targets MIBIB, BOOTCONFIG, APPSBL, ART or MTD0-MTD17.

The board-ID writer is gated by qcom,board_id so unrelated devices are not
changed. The tested CR8808 is XPA: IPQ5018 board ID 0x10 and QCN6122 0x60.
The third-party M81 ID255/calibration-variant selection is not used.

The corrected Linux 6.12 DTS/DSA/remoteproc path passed the scoped test on one
CR8808 M81. RF range, controlled Wi-Fi throughput, other CR880X variants and
long-duration behavior remain unverified.

Reference source: kmiit 9a11bb8; hzyitc original patch authorship in patches
998/999; ByteArray0 device commit 4f70a3bbd85f4 and qfprom 4299001. Provenance
is not a substitute for vendor board-data redistribution terms; see
PUBLIC_RELEASE_AUDIT.md.
