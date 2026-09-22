# Recovery

The tested CR8808 Web-Recovery U-Boot exposes a recovery page at
`192.168.10.1` when Reset is held during power-on. The listener was verified
without uploading an image and runs before Linux.

Only a factory UBI built for this bootloader/device belongs in Web Recovery; a
sysupgrade image is for a compatible running system. Keep a known-good factory
image and SHA256 on local storage before testing.

Recovery is manual. Tooling must never enter recovery, upload, repeat an
uncertain flash, change boot flags or reboot automatically. UART/programmer
access is last-resort recovery for bootloader/MIBIB damage, not an installation
prerequisite.
