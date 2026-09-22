# Attended 24.10 → 25.12 hardware test

This is an unverified hardware candidate, not a stable firmware announcement.
Do not use this runner on stock dual-slot, M79, another bootloader, or another
current software revision. It is deliberately restricted to the known-good
6.6.137 / r0-2b3c0919 CR8808 transition. Ethernet cable and physical access to
power/Reset are required; UART is not a normal prerequisite.

## Before authorization

The maintainer must complete clean build, static image/UBI/package checks,
runner tests and read-only hardware preflight. A local private
`$XDG_STATE_HOME/rainwrt/hardware-test.json` (default `~/.local/state`) records
candidate directory, candidate manifest SHA256 and Windows recovery directory.
This binds exact bytes, not a mutable filename. No self-registration occurs
when starting the runner. Do not turn an audit FAIL into a new trust anchor.

Keep the Windows-native known-good factory and checksum list available offline.
Known-good RainWrt recovery SHA256:
`7b48d723d93612c6fb8857ec4f05ac7faf62242f6848e5686f53fc8ff6752e69`.
The new candidate factory is not a proven recovery image.

## Execution contract

From the reviewed source checkout, the wrapper without arguments is a dry-run.
It may stage the exact image/config only in router `/tmp`, but performs no
NAND write or reboot. It creates standard configuration backup, transports it
as opaque bytes into a private mode-0600 local file, removes old opkg/APK
manager state and upgrade helpers, and checks the standard image validator.
There is no compressed image bundle upload or on-router image unpacking.

Only the user may invoke `--execute --validate-reboot` after a READY verdict.
The runner repeats all checks, reserves measured physical RAM and tmpfs space,
and calls sysupgrade exactly once. It never forces validation, changes boot
flags, retries installation, enters recovery or uploads a factory image.
The cloud agent is unnecessary after launch. Keep WSL and the computer awake.

SSH disappearing during ubus handoff is expected/indeterminate. Polling waits
up to ten minutes for a new boot ID. Old system, wrong build, missing critical
driver/package/layout/network conditions and host-key change are failures.
After all first-boot checks pass, the explicit reboot flag allows exactly one
normal `sync; reboot`, followed by the same checks. No successful second boot
means no HARDWARE_VALIDATED verdict. A persistent local attempt marker prevents
restarting the command from silently repeating a possibly completed flash.

The persistent marker is created **before the first remote execution attempt**,
including its last checks. It remains consumed even on `PRE_HANDOFF_FAILURE`:
missing output cannot prove that a write never started. A preflight failure
before that marker does not consume it. Dry-runs never consume it. Retrying a
consumed build requires explicit human investigation and a separately reviewed
marker reset; the runner never removes it or automatically permits a retry.

Resource gates distinguish running-system validation/handoff, subsequent ramfs
construction, and tmpfs capacity (see SYSUPGRADE_MEMORY_MODEL.md). They retain
the 8 MiB operational margin without reclaiming memory or stopping services.
Each gate requires two passing samples five seconds apart within a
120-second monotonic deadline, including sampling time. This applies before
archive collection, before payload upload with the exact archive budget, and
after upload and immediately before handoff. Only numeric memory probes repeat. A fresh final
resource check remains immediately before an explicitly authorized sysupgrade.

## Required checks

- Board, MTD18 character device/name/size/offset, no rootfs_1, cmdline,
  MIBIB primary table, active APPSBL, bootcmd, SHA256 and sysupgrade -T.
- Exact `/etc/rainwrt-release`, kernel/target, rootfs UBI volumes, overlay mount,
  critical dmesg errors, both radios, remoteproc, BDF IDs, Ethernet ports/carrier.
- WireGuard executable/module ABI and all three APK packages; no private VPN.
- Baseline-aware IPv4/IPv6/default routes and DNS+HTTPS using multiple public
  endpoints. A single ICMP failure is not a flash failure.
- Opaque preserved custom service bytes and enabled state; upstream disabled
  state is parsed with a strict safe-name grammar and regenerated, never eval'd.

The runner does not prove Wi-Fi client throughput, RF range, WAN line rate,
WireGuard handshake with a private peer or a full recovery write. Those remain
separate observations. Performance collection is read-only.

## Failure and recovery

`PRECHECK_FAILED`: nothing flashed. Fix the stated resource/identity/config
problem before reconsidering. `RETURNED_OLD_SYSTEM`, `RETURNED_WRONG_BUILD`,
`POSTCHECK_FAILED` or `REBOOT_VALIDATION_FAILED`: stop; no write retry.
`FAILED_TO_RETURN` prints `USE_VERIFIED_WEB_RECOVERY` and stops.

Recovery is a human decision. Manually hold Reset while powering on, open the
previously verified bootloader page at `192.168.10.1`, and use only the verified
known-good factory if recovery is chosen. Never upload the sysupgrade tar there.
The verified listener is not evidence of a tested full factory restore. If
bootloader/MIBIB is damaged, this software recovery assumption no longer holds.

Logs, sysupgrade list and configuration archives stay outside Git in private
state. Do not publish them; no service contents or secret values belong in the
public report. A SHA256 is integrity evidence, not a signature or endorsement.
