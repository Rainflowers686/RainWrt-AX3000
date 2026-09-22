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
| ath11k smallbuffers | Removed | Unnecessary and caused a 25.12 Kconfig recursion. |
| RSSI workaround | Uncertain | Not copied without evidence Linux 6.12 still needs it. |
| Dual-slot upgrade | Retained | Restricted to recognized stock-size layout; untested here. |
| Big-rootfs upgrade | Rewritten | Full MTD/MIBIB/APPSBL/bootcmd fingerprint, fail-closed. |
| M79 V1 upgrade | Disabled | Requires an independent layout fingerprint. |

Imported commits preserve original authorship; RainWrt safety changes are
separate commits.
