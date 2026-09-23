# Public-release audit

**Verdict: PUBLIC_RELEASE_BLOCKED_BY_BDF_LICENSE.**

The GitHub source repository must remain PRIVATE until the device-specific
wireless board-data redistribution question is resolved. No binary Release is
authorized by this audit.

## Scope and privacy

The current tracked source contains generic device support and generic
configuration migration only. It contains no private router configuration,
VPN peer, credentials, Wi-Fi profile or deployment backup. The hardware and
performance records in HARDWARE_VALIDATION.md and PERFORMANCE.md contain
device/test facts only.

The privacy scanner checks tracked files and Git object history without
printing matched values. Its pattern set is not a proof that arbitrary secrets
are absent. The exact locally produced image, configuration archives, raw
flash dumps, build signing key, performance logs and package caches are not
tracked or release assets.

The earlier all-local-ref audit found historical private-context path/service
references in commits on non-release refs; it did not report a credential
value. The current downstream line was based on official ImmortalWrt v25.12.2,
and legacy/private refs must not be pushed. Do not push all refs or mirror
this repository. If the project is later made public, repeat the branch and
history audit on the exact proposed public refs; do not rewrite existing
provenance history without a separate reviewed plan.

## Board-data provenance and redistribution

The two CR8808-specific binary containers are:

- package/firmware/ipq-wifi/src/board-redmi_ax3000.ipq5018
  SHA256 a1d03029566e469ceee4d570324dfa015f3d01e351bc87c81329ffdd7a7c4186
- package/firmware/ipq-wifi/src/board-redmi_ax3000.qcn6122
  SHA256 91c689226aa5a3af853063452393055c5e764866fec707ccd504738314e75134

They were restored in RainWrt commit fdad22dbf from the byte-identical files
present in the kmiit 24.10 branch. ByteArray0's port has separate
xiaomi_cr880x-named data, with its own provenance; it is not interchangeable
or a licensing substitute. No explicit vendor-origin grant for the two
CR8808 containers was found in the reviewed provenance.

The inspected OpenWrt firmware_qca-wireless repository does not list these
exact Redmi files. The OpenWrt ipq-wifi package describes local board-data
overrides as interim until device-specific data is upstream and documents
submitting board data upstream:

- https://github.com/openwrt/firmware_qca-wireless
- https://github.com/openwrt/openwrt/blob/main/package/firmware/ipq-wifi/Makefile

The Qualcomm firmware package includes a binary redistribution notice for its
firmware payloads. That notice has not been established as a grant covering
these separate CR8808 board-data containers. A whole-repository GPL notice,
public availability in a downstream tree, or kmiit/ByteArray0 provenance does
not by itself resolve the vendor rights question. No exact, equivalent,
properly licensed upstream container was found. These board-specific files are
also not safely replaceable with a different model's BDF by name similarity.

Until written terms or an upstream properly licensed equivalent covers the
exact data, keep the source repository private and do not distribute images
containing the files.

## Feed and artifact handling

The hwtest1 audit verified release-matched signed APK indexes and an offline
dependency closure for the audited feature set. Build keys, opaque user
archives and router dumps must never be included in hosted CI or release
artifacts. This audit does not authorize publishing those local artifacts.

## Re-audit before public visibility

Before any visibility change:

1. Resolve and document board-data rights.
2. Scan the exact branch and tags proposed for publication, not all local refs.
3. Confirm private runtime configuration and all build/private-key artifacts
   are absent from tracked files, reachable history and CI outputs.
4. Confirm README links, provenance notices, image metadata and feed matching.

Until then the required status is PUBLIC_RELEASE_BLOCKED_BY_BDF_LICENSE.
