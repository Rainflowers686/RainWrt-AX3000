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

Verdict: `PUBLIC_RELEASE_BLOCKED` until final images/package indexes pass the
artifact scan and public push scope explicitly excludes legacy private refs.
