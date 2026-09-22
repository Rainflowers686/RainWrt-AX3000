# Upgrade safety

The current candidate authorizes only one mode:

1. `rainwrt-single-slot` uses upstream `nand_do_upgrade` only after matching
   board, MTD size/index, absent `rootfs_1`, cmdline, MIBIB, APPSBL and
   `bootmiwifi`. It rebuilds UBI on `rootfs` and does not change U-Boot env.
2. `legacy-dual-slot` is NOT authorized. Its reference functions remain, but
   the detector refuses it because this candidate DTS uses fixed merged
   partitions. A stock-layout profile needs separate evidence and testing.

Checks run at image validation and again before writing. M79 is explicitly
refused. No path writes MIBIB, BOOTCONFIG, APPSBL, ART or MTD0-MTD17.

Configuration preservation must use standard sysupgrade lists, treat custom
entries opaquely and reject restoration of stale feeds or old upgrade helpers.

The attended transition uses standard sysupgrade with a sanitized private
configuration archive. No `-F` / force option is used. Existing 24.10 helpers
perform the first write; `/lib/upgrade/*.sh` is copied by stage2 into RAM_ROOT.
The new image includes the new fail-closed helpers for future upgrades.

The runner never changes U-Boot flags or recovery state. SSH/ubus disconnect
after handoff is indeterminate, not immediate failure. One write attempt only;
10-minute bounded return monitoring requires a different boot ID and the exact
new build identity. A normal reboot is allowed only with `--validate-reboot`
and after all first-boot critical gates pass. It is never a recovery action.

RAM checks now use the phase model in SYSUPGRADE_MEMORY_MODEL.md, superseding
the original overlapping-userspace/full-ramfs formula. Tmpfs capacity and
physical availability have separate requirements. The 8 MiB operational margin
remains; anticipated userspace anonymous-memory release can cover only deferred
ramfs files, with a hard cap at their measured size. No kernel/slab, Wi-Fi DMA,
or page-cache reclamation credit is added. This is not an OOM guarantee.

Each gate requires two passing samples five seconds apart, bounded by 120
seconds. No service quiesce, manual drop_caches or overlay staging is used.
The image is charged once before upload and already resident afterward. The
original archive streams to WSL; the migrated archive is staged, then copied
once by sysupgrade -f. The small upgraded ELF closure is copied before handoff;
the rest of RAM_ROOT is copied only after upstream userspace cleanup.

There is no new platform_pre_upgrade memory-abort hook: plain return is not a
stage2 abort, and explicit exit can lead upgraded to reboot after services and
SSH have already gone. Final refusal belongs before the handoff instead.
