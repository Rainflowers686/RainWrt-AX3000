# Attended 24.10 → 25.12 hardware test

hwtest1 passed the scoped CR8808 first/second-boot checks on 2026-09-22 after
the wireless configuration ABI correction below. This is not a stable firmware
announcement or a claim of long-duration/RF/recovery-write testing.
Do not use this runner on stock dual-slot, M79, another bootloader, or another
current software revision. It is deliberately restricted to the known-good
6.6.137 / r0-2b3c0919 CR8808 transition. Ethernet cable and physical access to
power/Reset are required; UART is not a normal prerequisite.

## Resume an already installed candidate (no installation)

`--resume-validation` is mutually exclusive with `--execute`. It verifies the
existing exact-build execution marker and that execution's image/configuration
hash evidence, original baseline and network/service state. The currently
running build must exactly match the candidate identity, kernel 6.12.103, and
have a different boot ID from the 24.10 baseline. Missing or ambiguous evidence
fails closed. This branch never collects another sysupgrade archive, uploads an
image, calls the image validator or invokes sysupgrade. The execution marker
remains permanently consumed.

Without `--validate-reboot`, this mode only performs current-system checks and
can report FIRST_BOOT_VALIDATED, never HARDWARE_VALIDATED. With that explicit
flag, **all** first-boot checks including DNS/HTTPS, preserved service state and
wireless configuration bytes must pass before one normal reboot is allowed.
A separate persistent, exclusive, fsync'd validation-reboot marker is created
before the remote request. An uncertain result consumes the reboot attempt;
restarting the runner cannot silently reboot again. A prior reboot recorded by
the original runner also blocks another request. Second-boot checks must pass
before HARDWARE_VALIDATED. There is no automatic recovery or installation retry.

## CR8808 wireless configuration ABI

24.10's QCN6122 path `platform/soc@0/soc@0:wifi1@c000000` changed to
`platform/soc@0/b00a040.wifi` in this 25.12 device layer. Leaving the old path in
the preserved archive causes wifi detection to add a new default radio while
the restored user radio remains unmatched. This is a configuration migration
issue, not evidence of an absent PHY or a failed QCN6122 driver.

The fingerprint-gated archive migrator now changes only that exact wifi-device
path token. It does not depend on section names. Every other byte, including
SSID, key, channel, country, encryption and iface associations, is preserved.
An already-new path is idempotent; simultaneous old/new paths, duplicate old
paths, duplicate section/path definitions or unsupported UCI grammar fail
closed. Private option values are not interpreted or logged. Unrelated valid
wireless configuration is unchanged. This is not a general-purpose UCI editor.

Validation checks the two exact physical paths, one 2g/IPQ5018 mapping and one
5g/QCN6122 mapping, the matching UCI and netifd section sets, no stale third
radio, no pending/retry failure, and AP/hostapd health for enabled radios.
Intentionally disabled radios may remain disabled. Resume also compares the
entire wireless file against the executed archive plus only the ABI correction,
so disabling a user's enabled radio cannot mask a validation failure.

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
