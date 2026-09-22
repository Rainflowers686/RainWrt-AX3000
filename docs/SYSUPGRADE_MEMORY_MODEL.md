# Sysupgrade memory model — hwtest1, 2026-09-22

Scope: known-good 24.10 CR8808 to the frozen 25.12.2-hwtest1 candidate. This is
a phase-aware admission policy, not an upstream minimum-RAM specification or
an OOM guarantee. No live handoff, service stop, cache drop, flash or reboot was
used to develop it. Kernel/slab/ath11k/DMA allocations remain resident in every
phase; no savings from them are assumed.

## Source authority and two different executing systems

The first write runs the **installed 24.10** tools, not the candidate's tools.
The eight first-write scripts are bound to the known-good image hashes and
checked live before using this model. The official 25.12.2 source is commit
`4fc16f2985a358bd43bb522e43f05395fcbd6ed5`. Its stage2 and the known-good 24.10
stage2 have identical Git blob `5ce0b3549cf68d523bab774e01841044fd558c19`.
Sysupgrade differs in package-list handling and validation, not in this ordering.

Primary references:

- [ImmortalWrt v25.12.2 sysupgrade](https://github.com/immortalwrt/immortalwrt/blob/v25.12.2/package/base-files/files/sbin/sysupgrade): image staging, validation, configuration, upgraded bootstrap, ubus.
- [ImmortalWrt v25.12.2 stage2](https://github.com/immortalwrt/immortalwrt/blob/v25.12.2/package/base-files/files/lib/upgrade/stage2): service cleanup before ramfs construction.
- [Common helpers](https://github.com/immortalwrt/immortalwrt/blob/v25.12.2/package/base-files/files/lib/upgrade/common.sh): RAM_ROOT=/tmp/root; install_file skips already copied targets; install_bin adds libraries.
- [NAND helpers](https://github.com/immortalwrt/immortalwrt/blob/v25.12.2/package/base-files/files/lib/upgrade/nand.sh): tar payloads stream into UBI tools, not a second whole uncompressed image.
- [procd upstream](https://git.openwrt.org/project/procd/): locally inspected pinned 25.12 procd `58eb263d` and known-good `c59f2d80`, system.c, sysupgrade.c and upgraded/upgraded.c. system validates, stops services and execs upgraded; upgraded invokes stage2 then calls reboot even if stage2 returns failure.
- [2019 upstream Wi-Fi shutdown proposal](https://lists.openwrt.org/pipermail/openwrt-devel/2019-June/023337.html): illustrates kill-stage failure with some network setups; it is not a CR8808 RAM bound or authority to stop Wi-Fi here. The proposed wifi-down addition is absent from our pinned stage2.

The upstream low-memory branch at MemTotal <=32768 KiB does not skip the
initial service deletion for network/log/dnsmasq. Larger systems skip these
initial deletions, but kill_remaining subsequently targets remaining userspace.
No generic numeric MemAvailable threshold was found in these pinned scripts.
RAMFS_COPY_BIN and RAMFS_COPY_DATA extend the later copy closure.

## Six phases

I = candidate bytes rounded to 4 KiB pages; C = migrated gzip archive similarly
rounded; H = upgraded plus unique shared libraries; R = entire stage2 file
closure including H, unique targets and page rounding; U = running userspace;
K = resident kernel/nonreclaimable memory. H is a subset of R, never H+R.

| Phase | Persistent tmpfs allocations | Working allocations and live userspace | Capacity / physical consideration |
|---|---|---|---|
| 1 Before upload | Neither I nor C; original backup streams to WSL | Normal U, SSH, fingerprint/backup processes; K unchanged | Reserve tmpfs space for I+2C+R+metadata; physical budget must fund I while U is alive, not assume U already stopped |
| 2 Upload / -T / metadata | One I, then one C; small helper/metadata files | Normal U plus SCP/hash/tar/fwtool/json shell processes | No image decompression or archive upload duplication. -T without -f creates metadata, not a config archive or RAM_ROOT |
| 3 Accepted / handoff | I+2C+H: sysupgrade -f copies C to /tmp/sysupgrade.tgz; install_bin copies H | Normal U during validation/bootstrap, then procd service_stop_all/exec | H must be budgeted BEFORE cleanup; it is not the full R |
| 4 Cleanup | I+2C+H | stage2 terminates userspace, sleeps, drops reclaimable caches; upgraded/watchdog/stage2 survive | Image/config shmem and K are not freed by drop_caches. No extra credit for already-accounted page cache |
| 5 RAM_ROOT / pivot | I+2C+R, not I+2C+H+R | Copy/ldd tools and stage2; normal U is gone | /tmp mount is moved, not copied. Source code pages may be faulted again, so working margin remains |
| 6 NAND write | I+2C+R until normal upstream cleanup/reboot | tar/UBI writer pipelines, upgraded/watchdog and K | Payload is read from staged I. ubiupdatevol allocates a LEB buffer; formatter works in eraseblocks, not an image-sized buffer |

The image must ultimately be in /tmp: URL input downloads there and other
paths are copied there. Overlay staging cannot reduce the final physical
requirement and introduces coexistence/copy risks; it is not used.

## Measurements and empirical constraint

Live known-good R: raw bytes 4,066,552 (the old probe reported ~3,972 KiB),
page-rounded **4,196 KiB**, 74 unique files. H: **848 KiB**, four files.
Offline comparable closures: 24.10 4,188 KiB / H 848 KiB; 25.12.2 3,076 KiB /
H 792 KiB. Offline roots omit runtime resolver/lock files; do not relabel the
old 3,972 KiB measurement as a new-kernel measurement. The first transition
uses the live 24.10 numbers. Future 25.12 self-upgrades need their own live audit.

The retained successful first-install log records MemAvailable 33,456 KiB
before staging, 12,656 KiB afterward, tmpfs available 73,740 KiB, and a real
handoff. The user verified the subsequent 6.6.137 boot/UBI/reboot/network/radios.
This contradicts treating the old 16,136 KiB pre-handoff policy as a necessary
condition on this hardware. It does **not** prove 12 MiB is universally safe.

The old gate combined two R allowances and 8 MiB headroom while all normal
services were still running. One R is actual future files; the second was an
undifferentiated copy/allocator margin. That sum was neither an upstream rule
nor a measured simultaneous high-water mark. We withdraw that interpretation.

## New gates and explicit assumptions

Keep **W=8192 KiB**, the existing operational transient margin. This is an
explicit project safety allowance, not a number derived as a universal upstream
minimum. It covers validation/SSH/shell/JSON/backup transients and later
copy/page-fault/UBI work. It is not reduced to obtain PASS. Source inspection
finds streaming validation/writes (fwtool fixed metadata/signature buffers,
tar streams, UBI eraseblock/LEB buffers), rather than another image-sized heap.
The dry-run must still exercise actual validation and post-upload availability.

Let A be unique global AnonPages minus an upper bound of the observer ancestry
including PID1 RssAnon. RSS is **not** summed over services: shared pages would
be counted repeatedly. If swap or locked/unevictable memory exists, use no
credit. Otherwise Q=min(R,max(A,0)). Q can cover only deferred RAM_ROOT file
allocation, never W, H's pre-cleanup need, image pages or kernel memory.
This projection assumes the pinned stage2 successfully clears normal userspace
and there are no unreported long-term pins retaining its anonymous pages.
If that assumption fails, preflight cannot guarantee memory or completion.
No dry-run observes the actual phase-4 high-water mark. MemAvailable itself is
an estimate; changing workloads remain a risk. Two passing samples are required.

P = configuration copies **not yet resident**: 2C before payload upload, C
after the migrated archive is staged (the other C will be copied by sysupgrade).
I_pending is I before upload and zero after exact-hash reuse/upload.

```text
running-system need       = H + W + P
post-cleanup ramfs need   = R + W + P
physical required        = I_pending + max(H + W + P, R + W + P - Q)
tmpfs capacity required  = I_pending + 2*R + P
```

The second R in **capacity only** conservatively covers metadata, directory
entries and temporary files. It is not claimed as simultaneous physical page
usage. Capacity cannot substitute for MemAvailable; both gates must pass.
Kernel/slab/Wi-Fi memory, cache reclamation and service file-backed RSS receive
zero additional physical credit. Credit is capped even when A is much larger.

For the measured closures and adequate eligible A, before C is known:
physical = 18,152 + 848 + 8,192 = **27,192 KiB**;
capacity = 18,152 + 2*4,196 = **26,544 KiB**.
If A is zero, physical rises to **30,540 KiB**. Unknown archive size is not
ignored: the gate repeats with actual C before upload. Post-upload I and C
already reduce the sampled available figures and are not charged twice.

Implemented stages: PRE_UPLOAD_CAPACITY_PHYSICAL_GATE, PRE_PAYLOAD_UPLOAD_GATE,
POST_UPLOAD_VALIDATION_GATE, PRE_HANDOFF_GATE. Each uses two passing samples
five seconds apart within 120 seconds. A fresh equivalent shell check executes
immediately before a separately authorized sysupgrade. All probes are read-only.

## Why no stage2 abort hook or service quiesce

platform_pre_upgrade runs after TERM/KILL/cache reclamation, before
switch_to_ramfs. stage2 has no set -e and does not test the hook's status, so
return 1 does not prevent the write. Explicit exit aborts stage2, but services
and SSH are gone; upgraded's callback finishes its loop and main calls reboot.
An abort is not a safely resumable shell session. We add no hook or new failure
mode there. Existing NAND/layout checks remain unchanged.

No transient service quiesce was needed to implement this model. It remains
unimplemented: no private service names, Wi-Fi/FDB assumptions or recovery of
service states are introduced. No manual drop_caches is issued.

## Package footprint decision

Files are audited without executing candidate binaries or modifying the original rootfs.
The differential repack is not a flashable image. Matching signed APK indexes
and offline dependency fetch are tested, not assumed from package filenames.

Installed-size is from the actual APK database. Differential SquashFS uses the
same xz preset/options and 256 KiB blocks, removing only each package's listed
payload; APK metadata remains. Fragment sharing makes differences non-additive.
The repacked baseline is 13,063,968 bytes vs original 13,063,894 bytes, a 74-byte
metadata/repack difference. Full dependency lists and reproducible script output
are retained in the local footprint JSON.

| Package | Class | Installed bytes | Differential compressed bytes | Dependency / decision |
|---|---|---:|---:|---|
| luci | USER-FACING required | 1 | 0 | Meta-package; closure includes LuCI modules, rpcd, uhttpd, ucode and libraries |
| luci-i18n-base-zh-cn | USER-FACING required | 146007 | 49360 | luci-base/ucode/rpcd closure; keep |
| luci-ssl-openssl | USER-FACING required | 1 | 0 | Meta-package; LuCI + libustream-openssl/libopenssl3/px5g-openssl; keep |
| kmod-wireguard | CORE_RUNTIME | 99814 | 28016 | Matching kernel + crypto/udptunnel modules; keep |
| wireguard-tools | CORE_RUNTIME | 58116 | 21486 | kmod-wireguard + libc; keep |
| luci-proto-wireguard | USER-FACING required | 35915 | 8205 | wireguard-tools, resolveip, ucode, QR support; keep |
| wpad-openssl | CORE_RUNTIME | 1874355 | 723463 | hostapd-common, OpenSSL, libnl/libubox/ubus, ucode modules; keep |
| curl | DIAGNOSTIC_OPTIONAL, runner-required | 160011 | 58952 | libcurl4, CA, OpenSSL, nghttp2, zlib; keep |
| ca-bundle | CORE_RUNTIME | 182193 | 105161 | System TLS trust bundle; keep |
| tcpdump | DIAGNOSTIC_OPTIONAL | 906876 | 283468 | libpcap1 + libc; optional, not a boot requirement |
| iperf3 | DIAGNOSTIC_OPTIONAL | 8171 | 1068 | libiperf3 + libatomic1 + libc; most payload is in its library |
| jq | DEVELOPER_OPTIONAL, presently runner-required | 356462 | 113624 | libc; keep while hardware probe consumes JSON |
| htop | DIAGNOSTIC_OPTIONAL | 287094 | 103140 | libncurses6 + terminfo + libc; optional |
| nano | USER-FACING optional | 151675 | 61684 | libncurses6 + terminfo + libc; optional |

CORE_RUNTIME: required network/Wi-Fi firmware and drivers, wpad-openssl,
WireGuard module/tools, CA/TLS and upgrade/recovery tools. USER-FACING required:
LuCI, Chinese translation, HTTPS LuCI and luci-proto-wireguard. curl remains
required by the hardware-test DNS/HTTPS checks. No private configuration is added.

Removing tcpdump/iperf3/htop/nano and exclusively used libpcap1/libiperf3/
libatomic1/libncurses6/terminfo saves **736,874 bytes (~720 KiB)** in the combined
repack. jq is not included in that removal set. The optional packages and their
dependencies can be fetched offline against the matching signed indexes without
allow-untrusted. Those tools have no always-running service in this image;
installed bytes do not equal permanently allocated RAM. Deleting them would
mainly save image/tmpfs pages and flash space, not their advertised installed
size as runtime RAM.

Decision: do not churn/rebuild the frozen hwtest1 for this modest saving. Keep
selection unchanged for this test; consider an optional diagnostics profile in
a later release. Thus old/new sysupgrade bytes remain **18,585,872**, old/new
SquashFS bytes remain **13,063,894**, and rootfs_data/autoresize is unchanged.
No experimental repack is placed in the release directory or offered for flash.

The audit did find a runner dependency correctness issue: this jq build omits
Oniguruma, so the probe's previous capture(regex) identity parser would fail on
the new system. The probe now uses split/slice only; exact identity comparison
still occurs on the host. No device-layer or firmware change is involved.
