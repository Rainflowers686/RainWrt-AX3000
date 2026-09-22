#!/bin/sh
set -eu

root="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$root"
base="${1:-upstream/immortalwrt-v25.12.2}"
private_pattern='ouc-net|ouc-portal|xha\.ouc\.edu\.cn|100\.69\.|校园网|/etc/ouc-|private-router-backups'

tracked_hits="$(git grep -Il -E "$private_pattern" -- . \
	':!docs/PUBLIC_RELEASE_AUDIT.md' \
	':!scripts/audit-public-release.sh' 2>/dev/null | wc -l)"
history_hits="$(git log --all-match -G "$private_pattern" --format='%H' "$base..HEAD" -- . \
	':!docs/PUBLIC_RELEASE_AUDIT.md' \
	':!scripts/audit-public-release.sh' | sort -u | wc -l)"
dump_hits="$(git ls-files | grep -Ec '(^|/)(mtd[0-9]+\.(bin|dump)|sysupgrade-backup.*\.(tar|tgz|gz))$' || true)"
status=PASS
[ "$tracked_hits" -eq 0 ] || status=FAIL
[ "$history_hits" -eq 0 ] || status=FAIL
[ "$dump_hits" -eq 0 ] || status=FAIL

printf '{\n'
printf '  "status": "%s",\n' "$status"
printf '  "base": "%s",\n' "$base"
printf '  "tracked_private_pattern_files": %s,\n' "$tracked_hits"
printf '  "history_private_pattern_commits": %s,\n' "$history_hits"
printf '  "tracked_dump_files": %s\n' "$dump_hits"
printf '}\n'
[ "$status" = PASS ]
