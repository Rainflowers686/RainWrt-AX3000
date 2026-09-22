# hwtest1 checkpoint — 2026-09-22

Status: `BUILD_READY`, `STATIC_STRUCTURE_PASS`, `NOT_READY_FOR_ONE_COMMAND_HARDWARE_TEST`.
No router flash/reboot/recovery was performed by this audit.

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
