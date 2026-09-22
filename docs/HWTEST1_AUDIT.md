# hwtest1 checkpoint — 2026-09-22

Current status: `BUILD_READY`, `STATIC_STRUCTURE_PASS`, `READY_FOR_ONE_COMMAND_HARDWARE_TEST`.
No router flash/reboot/recovery was performed by this audit.

## Phase-aware follow-up (2026-09-22)

This supersedes the resource blocker below; the earlier evidence is retained.
SYSUPGRADE_MEMORY_MODEL.md independently compares pinned upstream and installed
24.10 first-write lifecycles. Full ramfs construction follows service cleanup;
only upgraded's smaller closure is copied before handoff. The original 8 MiB
operational margin remains. Tmpfs capacity and physical availability are now
separate gates, with bounded credit only for deferred files after userspace
cleanup. No manual service/cache/VM changes or stage2 abort hook were added.

Live default dry-run completed LOCAL_PREFLIGHT_PASS, all fingerprints, eight
existing helper hashes, config list/archive collection, opaque migration,
candidate transfer and SHA, detector=rainwrt-single-slot, sysupgrade -T,
board/target metadata, stage2 helper checks, post-upload memory, IPv4/IPv6
DNS/HTTPS baseline, PREFLIGHT_PASS and DRY_RUN_COMPLETE. The final repeat reused
the exact already-uploaded image by SHA instead of making a second tmpfs copy.
No execute marker was created and no execute/reboot flag was supplied.

Actual archive audit: five core configs and two SSH host keys byte-preserved,
old opkg/APK/upgrade/rc.d state excluded, five members removed, one preserved
custom enabled service prepared, 73 final members / 23,222 compressed bytes.
Private archive content and service names are not in this document or delivery.
Gzip CRC and tar parsing passed. Private archive hashes remain in private/local
test evidence, not in the public candidate.

Pre-payload upload passed at MemAvailable 32,432 / 31,532 KiB against 27,240
KiB physical and 26,592 KiB capacity requirements. Post-upload passed at 23,388 /
17,896 KiB; pre-handoff passed at 16,320 / 16,200 KiB, tmpfs free 73,816 KiB.
Post-upload requirements were 9,064 KiB physical / 8,416 KiB capacity; even with
zero projected anonymous-memory credit, both final samples exceed the full
12,412 KiB ramfs-phase requirement. A fresh equivalent shell guard also passed.

Two generic runner bugs surfaced only after clearing the original resource gate:
non-executable S-link targets are not enabled boot services (procd execlp would
fail), and OpenWrt libraries intentionally reference unset optional variables,
so detector sourcing now runs in a nounset-disabled subshell while the outer
guard remains strict. Regression cases cover both. Package audit also corrected
the probe identity parser to work with the candidate's regex-free jq build.

31 runner tests, shell suites, syntax/ShellCheck, source-order and cross-language
memory-gate tests PASS. Frozen candidate structure/module/feed audit PASS.
Optional diagnostics plus exclusive dependencies save only 736,874 bytes in a
non-bootable differential SquashFS experiment; selection and all firmware bytes
remain unchanged. Twelve optional-package dependency APKs fetched from matching
signed local indexes without bypassing trust. CI lint/packaging includes the new
memory helper and model; hosted CI was not run.

Readiness is for an attended hardware experiment, not hardware validation or
public-release approval. Anonymous-memory release is projected, not measured
after an actual handoff; workloads can change. Existing firmware/device risks
and the distinct public-release blockers remain. Recovery assets retain their
known-good hashes; no recovery write was performed.

## Resource follow-up (2026-09-22, 11:44–11:51 UTC)

This follow-up supersedes the earlier no-cleanup authorization and resource
snapshot below; it does not replace the firmware or erase the prior evidence.
Only the expressly authorized old attended staging was removed after checking
its known-good image SHA256, non-symlink/canonical path, tmpfs mount and two
process cwd/root/fd scans (zero references). Its 18,088 KiB can be restaged from
the untouched local known-good assets. No other temporary directory was deleted.

Tmpfs used/free changed from 18,540/73,936 KiB to 452/92,024 KiB. Immediately
after deletion MemAvailable was 27,160 KiB, not enough for 34,287 KiB. The new
runner waited the full 120 seconds with 24 fresh samples: 23,972–26,784 KiB,
zero passing samples. It exited PRECHECK_FAILED before configuration collection,
candidate upload, sysupgrade -T, or any execute attempt. Fingerprint checks and
LOCAL_PREFLIGHT_PASS passed. CONFIG_MIGRATION_LIVE, SYSUPGRADE_T_LIVE and
POST_UPLOAD_MEMORY remain BLOCKED, not PASS. No execute marker was created.

Read-only follow-up: stage2 closure 3,972 KiB; unchanged reserve 16,136 KiB;
upload 18,151 KiB. Tmpfs later used only 460 KiB. The remaining old installer
temporary directory is 128 KiB, too small to close the gap and was left alone.
Slab was 32,996 KiB (5,992 reclaimable / 27,004 unreclaimable), page cache
20,524 KiB, AnonPages 8,260 KiB; largest process RSS 7,304 KiB. Summed process
RSS 44,036 KiB double-counts shared mappings and is not physical memory use.
No private process names, command lines or configuration contents were logged.

The live min_free_kbytes is 16,384, consistent with the upstream init script.
MemFree therefore must not substitute for MemAvailable; kernel watermarks are
not spare upgrade headroom. Ath11k page/DMA allocations cannot be attributed
exactly from these counters (zero ath11k-labeled vmalloc entries is not zero
Wi-Fi memory use). No services, caches, VM settings or radios were changed.
No avoidable runner image double-copy exists: no candidate is staged yet;
the original config streams to WSL, and only the migrated archive is uploaded.
The two stage2/config allowances remain intentional margins/copies, not a
second image charge. There is no evidence-based lifecycle saving sufficient
to clear this gate under the present authorization.

The final full probe still showed the original boot ID, increasing uptime,
unchanged MTD/MIBIB/APPSBL/bootcmd, stage2 3,972 KiB, and MemAvailable 31,696 KiB
(still below the requirement). Stage2 helper copy-chain source checks passed.
Both Windows-native known-good recovery images still match their frozen hashes;
the historical recovery listener validation is not a new recovery-write test.

Tests: 25 runner unit cases PASS, including all four resource-stability cases,
deadline accounting, archive CRC/core/key preservation and exclusive execution
marker; layout/dualboot/handoff/write-scope shell suites PASS; shell syntax and
tooling ShellCheck PASS; candidate static audit PASS (112 modules, four signed
indexes, 87-package dependency closure); refreshed delivery checksums PASS.
Public-branch pattern scan PASS with existing policy-text classifications only.
No DTS/BDF/kernel/package changes or rebuild. Status remains
`NOT_READY_FOR_ONE_COMMAND_HARDWARE_TEST`: physical RAM gate unmet.

## Earlier build and pre-cleanup evidence

Firmware source: `ff21ae557201e2def1ca4770275abca2fdae477f`.
Upstream: ImmortalWrt v25.12.2 `4fc16f2985a358bd43bb522e43f05395fcbd6ed5`.
Build ID: `25.12.2-hwtest1-ff21ae557201-45d16c23d08e`.
Kernel: 6.12.103; qualcommax/ipq50xx; redmi_ax3000.
Subsequent commits contain tooling/audit/docs only, not a claim that the image
was rebuilt from their HEAD.

| Image suffix | Bytes | SHA256 |
|---|---:|---|
| squashfs-sysupgrade.bin | 18585872 | 98099b26672fdb0931a30673792402f42194dbac66a559520596d4b86e58121c |
| squashfs-factory.ubi | 19529728 | 55ddb80a463466f2375815df8ab67ecea53e66dfc8ee0ef0719fb17a39c1ebac |
| initramfs-uImage.itb | 18486076 | 37caf642c0c462e83c4474245b2472cf20fec7068198ce16ce79738d55864b45 |

Prefix: `immortalwrt-qualcommax-ipq50xx-redmi_ax3000-`.
Full clean source build after clearing only its interrupted build outputs:
991.88 seconds, exit 0. A host WSL restart interrupted earlier attempts and
left an empty host xz executable; those attempts are not counted as PASS.
Git object integrity was separately rechecked. Known-good images are unchanged.

Static: UBI EC/VID/table CRCs valid; kernel and effective SquashFS payloads
match the sysupgrade image; rootfs_data volume exists with autoresize. Runtime
identity matches manifest. All 112 modules use kernel 6.12.103. WireGuard,
wpad-openssl, LuCI, Chinese LuCI and both radio firmware/BDF packages are in
the image. The smallbuffer define is present in actual ath11k compiler command
records, not just .config. FIT default config is `config@mp02.1`, gzip kernel,
load/entry `0x41000000`; this is not an authorization to RAM-boot it.

Offline tests: runner handoff/return/reboot/migration cases; real detector
fingerprints; mocked platform write dispatch; stage2 helper glob; shell syntax,
ShellCheck, diff whitespace; real APK 3 positive/negative lookup, signed-index
verification and dependency fetch; extracted-image/privacy patterns. GitHub
hosted CI was not run; its workflow and local build entry point were checked.

Runner unittest count: 18, with a 21-condition failure matrix and explicit
wrong-image/manifest tests. New tooling ShellCheck is clean. Full inherited
board/platform scripts still report upstream SC2046/SC2086 quoting and
SC2155/SC2181 style warnings; these are not represented as a full-tree lint
PASS or changed merely to obtain a green number. Syntax checks pass. Current
eight first-write sysupgrade/stage2 files were independently compared by hash
with the immutable known-good image and match; runner binds those exact hashes.

Live read-only preflight: board, exact MTD18 geometry, MIBIB, active APPSBL,
cmdline, bootcmd and source identity passed. Router boot ID remained continuous
through the audit; MTD/APPSBL unchanged. Latest runner dry-run stopped before
upload: MemAvailable 16404 KiB versus required 34287 KiB (18151 KiB image plus
16136 KiB measured reserve); tmpfs free 73940 KiB. No upload, on-router image
unpacking, config migration or sysupgrade -T occurred after this gate.

Existing old RainWrt staging accounts for roughly 18 MiB of tmpfs use, but this
turn's read-only authority does not authorize deleting it. No unrelated /tmp
files were removed. Do not lower the RAM requirement to obtain a PASS. After
an explicitly authorized safe resource cleanup, repeat default dry-run before
considering the execute flag. Full live config-preservation and image-check
gates therefore remain pending, not PASS.

Separate public-release gate: see PUBLIC_RELEASE_AUDIT.md (legacy-ref privacy
boundary and explicit BDF redistribution provenance). Hardware behavior on
6.12, RF quality, high-load memory stability and normal reboot persistence
remain untested. The 24.10 evidence is retained, not silently relabeled as 25.12.
