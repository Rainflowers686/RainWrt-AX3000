#!/bin/sh
set -eu

script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck source=scripts/lib/attended-install-state.sh
. "$script_dir/../scripts/lib/attended-install-state.sh"
failures=0
fixture="$(mktemp -d /tmp/rainwrt-handoff-test.XXXXXX)"
trap 'rm -rf "$fixture"' EXIT

assert_eq() {
	if [ "$1" = "$2" ]; then
		echo "ok - $3"
	else
		echo "not ok - $3: expected $1, got $2"
		failures=$((failures + 1))
	fi
}

: > "$fixture/empty"
printf '%s\n' 'Commencing upgrade. Closing all shell sessions.' > "$fixture/handoff"
assert_eq PREFLIGHT_FAILED "$(rainwrt_preflight_state 1)" 'preflight failure'
assert_eq PRE_HANDOFF_FAILURE "$(rainwrt_handoff_state 1 "$fixture/empty")" 'failure before handoff'
assert_eq EXPECTED_HANDOFF "$(rainwrt_handoff_state 246 "$fixture/handoff")" 'status 246 after handoff'
assert_eq SUCCESS "$(rainwrt_return_state 1 1 0)" 'new system returned'
assert_eq RETURNED_OLD_SYSTEM "$(rainwrt_return_state 1 0 0)" 'old system returned'
assert_eq FAILED_TO_RETURN "$(rainwrt_return_state 0 0 0)" 'timeout'
assert_eq POSTCHECK_FAILED "$(rainwrt_return_state 1 1 1)" 'postcheck failure'
exit "$failures"
