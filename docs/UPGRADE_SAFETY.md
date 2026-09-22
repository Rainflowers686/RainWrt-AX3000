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

RAM budget is measured, not inferred from tmpfs capacity: twice the stage2
binary/library/script closure plus 8 MiB transient headroom plus two config
archive copies. Before upload, add image size. Both MemAvailable and tmpfs
free space must pass. This is a conservative lower bound, not an OOM guarantee.
Each preflight resource gate requires two consecutive passing samples at least
five seconds apart, with a 120-second deadline; a low sample resets the streak.
Sampling waits do not change the reserve, reclaim caches, or stop services.
The image is counted only before upload (and only if its exact bytes are not
already staged); after upload its memory is already reflected in MemAvailable.
The streamed original configuration archive remains only on the local host;
only the migrated archive goes to `/tmp`. Two archive-copy allowances cover
the staged input and sysupgrade's configuration copy. Stage2's second closure
allowance is intentional allocation/copy margin, not a second image charge.
