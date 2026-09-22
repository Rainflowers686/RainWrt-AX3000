# Public release audit

The public 25.12 line starts from official ImmortalWrt v25.12.2 rather than the
private legacy branch.

PASS: no institution-specific authentication, private route, Wi-Fi setting,
WireGuard secret, endpoint or backup dump is part of firmware logic. WireGuard
is capability-only. Feeds are commit-pinned. Private router backups remain
outside the repository.

The older local `rainwrt/baseline-wg` tooling history once named private
configuration paths while checking preservation. No private values or dumps
were identified, but that branch must not be pushed wholesale. Publish only
reviewed public-branch commits/tags, never all local refs.

Final source, history, extracted sysupgrade rootfs, factory UBI and package
manifest scans passed without private-pattern or private-key findings.

Verdict: `PUBLIC_RELEASE_READY` for the reviewed 25.12 branch only. This does
not make the untested 25.12 image hardware-stable, and it does not authorize a
push of legacy private refs.
