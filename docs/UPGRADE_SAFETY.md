# Upgrade safety

Two mutually exclusive modes exist:

1. `rainwrt-single-slot` uses upstream `nand_do_upgrade` only after matching
   board, MTD size/index, absent `rootfs_1`, cmdline, MIBIB, APPSBL and
   `bootmiwifi`. It rebuilds UBI on `rootfs` and does not change U-Boot env.
2. `legacy-dual-slot` requires the recognized stock-sized rootfs pair, writes
   the inactive UBI, then uses vendor slot flags. It is not verified on the
   current single-slot unit.

Checks run at image validation and again before writing. M79 is explicitly
refused. No path writes MIBIB, BOOTCONFIG, APPSBL, ART or MTD0-MTD17.

Configuration preservation must use standard sysupgrade lists, treat custom
entries opaquely and reject restoration of stale feeds or old upgrade helpers.
