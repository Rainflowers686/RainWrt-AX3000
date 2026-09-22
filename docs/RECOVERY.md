# Recovery

The tested CR8808 Web-Recovery U-Boot exposes a recovery page at
`192.168.10.1` when Reset is held during power-on. The listener was verified
without uploading an image and runs before Linux.

Only a factory UBI built for this bootloader/device belongs in Web Recovery; a
sysupgrade image is for a compatible running system. Keep a known-good factory
image and SHA256 on local storage before testing.

Recovery is manual. Tooling must never enter recovery, upload, repeat an
uncertain flash or change boot flags. An explicitly requested normal reboot
validation after a successful upgrade is distinct from recovery. UART/programmer
access is last-resort recovery for bootloader/MIBIB damage, not an installation
prerequisite.

Listener entry was demonstrated, not a full destructive restore. Keep the
known-good 24.10 factory and the older reference factory on native Windows
storage with verified SHA256. If the candidate fails to return, stop the runner
and decide manually whether to use Reset + power-on and a browser at the
bootloader address. Never upload a sysupgrade tar to the recovery page. Do not
assume the untested new factory is a proven recovery asset.
