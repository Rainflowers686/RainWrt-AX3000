# kmiit device delta

Reference: `kmiit/Redmi_AX3000_immortalwrt`, base
`9a11bb83d22efd5879439427cd222b957f6f7019`.

| Area | Disposition | Notes |
|---|---|---|
| Target/image | Forward-ported | Modern IPQ5018 DTS/UbiFit; `redmi,ax3000` retained for M81. |
| IPQ5018/QCN6122 remoteproc/memory | Newer API | Based on maintained 6.12 DTS; hardware test required. |
| QCA8337 dual CPU links | Required | 6.12 DSA fixes retained with authorship. |
| PHY DAC/PHY-to-PHY | Newer API | Expressed by 6.12 DTS and DSA patches. |
| PA-dependent IPQ5018 board ID | Required | EPA `0x24`; XPA/IPA/default `0x10`. |
| QCN6122 board data | Required | Board package/caldata path retained; `0x60` was verified on 24.10. |
| ath11k smallbuffers | Rewritten | Restore known-good ring limits with a CR8808-only boolean, not a recursive package variant. Memory mode 2 keeps 4 vdevs / 32 peers. Hardware validation remains required. |
| RSSI workaround | Already in port | Patch 947 handles IPQ5018/QCN6122 station RSSI. No duplicate patch. |
| Dual-slot upgrade | Disabled | Current DTS fixes a merged layout; stock writes require a separately verified profile. Functions retained as reference only. |
| Big-rootfs upgrade | Rewritten | Full MTD/MIBIB/APPSBL/bootcmd fingerprint, fail-closed. |
| M79 V1 upgrade | Disabled | Requires an independent layout fingerprint. |

Imported commits preserve original authorship; RainWrt safety changes are
separate commits.

## Independent re-audit corrections (hwtest1)

The earlier candidate restored `redmi,ax3000` in the DTS but missed matching
caldata (both radios), Ethernet, LED and environment-reader board cases.
All are now aligned. Ethernet aliases preserve the reference eth0/eth1 order.
The active APPSBL is mtd12, not mtd11; mtd0–mtd17 are read-only in the DTS.

The hotplug board-ID writer needs the ath11k DT/filesystem override consumer.
Both hzyitc changes are forward-ported in patch 998; requests are gated by
`qcom,board_id`, avoiding changes to unrelated devices. Exact unmodified kmiit
BDF containers are restored: IPQ5018 EPA 0x24 / XPA or IPA 0x10; QCN6122 0x60.
The third-party M81 ID255/calibration-variant selection is not used.

The IPQ5018 byte-wide qfprom read fix is restored conditionally. Unrelated
qfprom devices retain upstream behavior; no thermal protection is bypassed.
Imported Linux 6.12 DTS/DSA/remoteproc APIs remain, so RF, PHY ordering, memory
pressure and restart behavior are still hardware-test requirements.

Reference source: kmiit 9a11bb8; hzyitc original patch authorship in 998/999;
ByteArray0 device commit 4f70a3bbd85f4 and qfprom 4299001. Original attribution
is not a substitute for vendor BDF redistribution terms; see release audit.
