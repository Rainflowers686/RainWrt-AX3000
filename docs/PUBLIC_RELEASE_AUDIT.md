# Public release audit — hwtest1 independent review

Verdict: **PUBLIC_RELEASE_BLOCKED**. This supersedes the earlier blanket READY
claim. A passing pattern scan is not proof of arbitrary secret absence or a
license clearance.

## Rechecked scope

The public branch starts at official v25.12.2, not the private legacy fork.
The scanner checks tracked bytes and Git blob history, reports only paths,
object IDs and finding types, and fails closed on subprocess/read errors.
Secret-pattern rules have no file exemptions. Context terms in the scanner
and this policy are classified as policy text, not silently excluded.

Public branch-delta and extracted hwtest1 rootfs scans: no private-context,
private-key block, credential-token, WireGuard-key or dump-name finding outside
policy definitions. Factory rootfs matches the sysupgrade SquashFS payload.
Opaque user archives are not in the candidate. No ImageBuilder/SDK was built.
The preserved legacy first-install bundle's small text members also have no
private-context match. These scans cannot recognize every possible password.

Generic hostapd RADIUS support and its unconfigured init script are upstream
features, not user-specific authentication, and are retained. No private
service name, address, credential, VPN configuration or institution-specific
behavior is added to the public firmware/runner.

## Reachable history risks

All-local-ref scan reviewed 47868 files/blobs before the final tooling commit.
It found private-context references, not a demonstrated credential value:

| Path | Blob | Relevant commits | Type |
|---|---|---|---|
| scripts/attended-first-install.sh | 59e802892f5f607ce1d85327d418d2a1f11ec033 | dec2111ab, 444a3ee6c | historical user-environment checks |
| .gitignore | 2ef70a34be436390456ff9a5578213f84cf6c459 | 2b3c09192 | private backup path reference |
| .gitignore | 0ec4cf2f19948799c7331495d5dd0a1587ce9ac4 | f1bdf4900, 2b3c09192 | private backup path reference |

Do not push `--all`, mirror this repository, or publish legacy refs. No history
was rewritten and no known-good objects were removed. A future release should
use an explicitly reviewed public-branch-only clone; do not blindly sanitize
or overwrite the hardware reference history.

## License/provenance gate

Imported source retains author/commit provenance and upstream licenses. The
Qualcomm firmware's binary redistribution notice is copied into the candidate;
it permits unmodified use on Qualcomm chipsets subject to its conditions, not
GPL relicensing. Exact kmiit BDF bytes were restored and verified against the
image, but an explicit vendor-origin redistribution grant for those two BDF
containers has not been established by this review. A repository-wide GPL
notice alone does not settle vendor board-data rights. This is a public-release
blocker; no publication occurred. Resolve provenance/terms or obtain an
upstream properly licensed equivalent before distributing a public release.

## Feed trust

Four APK indexes verify against the candidate's public key. A fully offline
recursive fetch of 87 packages for the audited feature set succeeds without
trust bypass. Individual APKs are unsigned by upstream design and are bound
by the signed index; standalone package verification is not the feed trust
test. Signing private keys, user archives, raw logs and router dumps must never
be included in CI/Release artifacts. No mismatched official core feed is
enabled; the full matching local feed is retained.
