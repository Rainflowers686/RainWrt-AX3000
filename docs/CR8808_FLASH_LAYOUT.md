# CR8808 flash layout

The verified CR8808 retains the stock dual-slot partition table in MIBIB. Its
custom Web-Recovery APPSBL changes the runtime FDT so Linux instead exposes one
contiguous partition: start `0x00a80000`, size `0x07480000`, end-exclusive
`0x07f00000`, runtime `mtd18` named `rootfs`.

The single rootfs is therefore a bootloader FDT fixup, not a rewritten MIBIB.
Public hashes identify the known MIBIB table and APPSBL; no dump or sensitive
environment value is stored. Other CR880X bootloaders may expose stock slots or
another map, so board name alone never authorizes a write.
