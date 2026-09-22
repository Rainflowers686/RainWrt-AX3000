# Build identity

`scripts/prepare-rainwrt-build.py` requires clean Git HEAD, official base
ancestry and exact pinned feed revisions. It generates ignored build inputs
`files/etc/rainwrt-release` and `rainwrt-build-identity.json` before the build.
The build ID combines clean source commit and config-seed/feed digest. No
commit self-reference loop, username, host path, secret or private address is
embedded. Resolved config/buildinfo and exact image SHA256 accompany the image.

The hardware runner compares the complete runtime dictionary against the
reviewed local manifest, plus kernel, target, board, NAND/UBI and package gates.
A matching version banner alone is not enough. A build ID binds build inputs;
the SHA256 binds exact bytes. Neither is a claim of byte reproducibility or
hardware validation. Later tooling/docs commits are recorded separately from
the firmware source revision.

Release packaging must retain source identity, resolved config, pinned feeds,
all images, manifests, signed ABI-matched APK indexes and their checksum-bound
packages, public signing
key, vendor license notices and checksums. Never distribute the signing private
key or local user configuration archives. No official mismatched core feed is
configured in the candidate.

APK 3 individual packages from this upstream build are unsigned; the signed
repository index is their trust anchor. Standalone `apk verify package.apk`
therefore reports UNTRUSTED, while index verification and offline recursive
`apk fetch` through the retained trusted indexes succeed. Never bypass trust
using `--allow-untrusted`. The candidate audit exercises real APK 3 syntax and
a missing-package negative query, not opkg assumptions.
