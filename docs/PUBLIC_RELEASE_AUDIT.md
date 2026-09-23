# Public-release audit

**Source status:** `PUBLIC_SOURCE_READY=YES` after the sanitized public refs
pass the exact-ref audit described below.

**Board-data status:** `BDF_LICENSE_FINDING=REDISTRIBUTION_NOT_ESTABLISHED`;
`BDF_REDISTRIBUTION_STATUS=NOT_REDISTRIBUTED` in the public source tree.

**Binary status:** `PUBLIC_BINARY_RELEASE=BLOCKED` until redistribution rights
for the embedded board-data are established. This project must not upload
firmware images or matching package-feed artifacts as public releases.

This is an engineering release gate, not a legal opinion.

## Board-data findings

The CR8808 M81 build uses these exact inputs:

| Logical input | Path in the historical build tree | SHA256 | Radio / tested ID |
|---|---|---|---|
| Redmi AX3000 IPQ5018 | `package/firmware/ipq-wifi/src/board-redmi_ax3000.ipq5018` | `a1d03029566e469ceee4d570324dfa015f3d01e351bc87c81329ffdd7a7c4186` | IPQ5018 / `0x10` |
| Redmi AX3000 QCN6122 | `package/firmware/ipq-wifi/src/board-redmi_ax3000.qcn6122` | `91c689226aa5a3af853063452393055c5e764866fec707ccd504738314e75134` | QCN6122 / `0x60` |

The CR8808 pair was originally introduced by hzyitc commit
`c30f40f2a2fc3591e6b6af8d27ee353497889fcb`; the same Git blobs are present in
the kmiit `redmi_ax3000-24.10` line and were restored to RainWrt's hwtest1 line
in commit `fdad22dbf79f61f3f63f9271b87d212665d77fbe`. This establishes lineage,
not a vendor grant.

The separate, non-hwtest M79/CR880X reference pair was introduced by ByteArray0
in commits `4f70a3bbd85f4fbf0b61ad242aaed3ef09159fd7` and
`82234aa6a5854c39cd5e7527acdd88b37e52fe6f`:

| Historical input | SHA256 | Radio / status |
|---|---|---|
| `board-xiaomi_cr880x.ipq5018` | `2f6b42f7ab1e0b1bdd0ad8cffc98aa4f860036d2dff75a11a559c27496fc7ff6` | IPQ5018 / M79 reference, not hardware validated |
| `board-xiaomi_cr880x.qcn6122` | `467685a49e4d38f1a14c7d2387b4652ba013146b88c4ccf31c836621547166cb` | QCN6122 / M79 reference, not hardware validated |

This pair also has no established redistribution permission and is excluded
from the proposed public history. Exact CR8808 hashes and local build
requirements are in [BOARD_DATA.md](BOARD_DATA.md).

The current OpenWrt `firmware_qca-wireless` mirror listing has no exact Redmi
AX3000 or Xiaomi CR880X board-data entries. OpenWrt's `ipq-wifi` Makefile
describes device-specific files as interim while awaiting upstream availability
and directs contributors to submit them upstream. Neither fact grants rights
to third-party files already circulating in downstream repositories. A
Qualcomm/Atheros firmware notice or a Qualcomm license for a different payload
cannot be assumed to cover these specific board-data containers. The
linux-firmware project requires redistribution terms backed by an authorized
vendor provenance/sign-off; no such grant was identified for these exact
inputs. Sources reviewed:

- [OpenWrt firmware_qca-wireless](https://github.com/openwrt/firmware_qca-wireless)
- [OpenWrt ipq-wifi Makefile](https://github.com/openwrt/openwrt/blob/main/package/firmware/ipq-wifi/Makefile)
- [Qualcomm Atheros ath10k license example](https://kernel.googlesource.com/pub/scm/linux/kernel/git/tnguy/firmware/+/refs/heads/main/LICENSE.QualcommAtheros_ath10k)
- [linux-firmware licensing and provenance criteria](https://kernel.googlesource.com/pub/scm/linux/kernel/git/tnguy/firmware/+/refs/heads/main/)

Conclusion: redistribution is **not established** (traceable provenance, unclear
permission). No equivalent upstream BDF was selected or substituted.

## Sanitized public source design

- All four device-specific containers (CR8808 pair and M79 reference pair) are
  removed from the public source tree and from the history reachable from the
  exact public branch/tag refs.
- Historical key-like payload blobs found during the release scan were also
  removed from the candidate public history; payload contents were not copied
  into reports or documentation.
- CR8808 builds require the user's two locally supplied files under the
  Git-ignored `vendor-local/board-data/` directory.
- `scripts/local_bdf.py` checks exact filenames and SHA256, rejects symlinks,
  missing/extra files and conflicts, then copies verified files only into the
  temporary `ipq-wifi` package build directory.
- A clean checkout without those local files fails before feed updates or
  downloads, with the required paths and hashes.
- GitHub Actions performs source/privacy tests only. It does not build or upload
  firmware binaries or package feeds.

The public source tree is a redistribution-sanitized representation. The
hardware-tested firmware was built from source revision
`ff21ae557201e2def1ca4770275abca2fdae477f` using the exact board-data hashes
above. The sanitized public-source commit is not itself the source revision
that produced that firmware and has not been reflashed or independently
hardware-tested. The public-safe annotated validation tag preserves this
distinction.

## Privacy and history gate

Before changing repository visibility, run:

```sh
python3 scripts/audit_public_source.py \
  --ref main \
  --ref validated/cr8808-25.12.2-hwtest1-public-source-2026-09-22
```

The audit checks every object reachable from the named refs for the known
board-data blobs and paths, verifies that local inputs are ignored, and invokes
the secret/personal-context scanner over the complete reachable history of
those refs, including upstream ancestors, plus the current checked-out tree.
The scanner is a pattern audit, not proof that arbitrary secrets are absent.
Legacy/private branches remain local and must not be pushed.

The pre-rewrite repository is preserved in a permission-restricted local Git
bundle outside the project. Do not push it or any legacy ref. No public binary
release is authorized by this audit.
