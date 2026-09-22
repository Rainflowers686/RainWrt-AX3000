#!/bin/sh
# Pure classifiers: no network, reboot or storage side effects.

rainwrt_preflight_state() {
	[ "$1" -eq 0 ] && echo PREFLIGHT_OK || echo PREFLIGHT_FAILED
}

rainwrt_handoff_state() {
	status="$1"
	output_file="$2"
	if grep -Eq 'Commencing upgrade\. Closing all shell sessions\.|ubus call system sysupgrade' "$output_file" 2>/dev/null; then
		echo EXPECTED_HANDOFF
		return
	fi
	case "$status" in
		0|246|255) echo INDETERMINATE_HANDOFF ;;
		*) echo PRE_HANDOFF_FAILURE ;;
	esac
}

rainwrt_return_state() {
	returned="$1"
	identity_matches="$2"
	postcheck_status="$3"
	[ "$returned" -eq 1 ] || { echo FAILED_TO_RETURN; return; }
	[ "$postcheck_status" -eq 0 ] || { echo POSTCHECK_FAILED; return; }
	[ "$identity_matches" -eq 1 ] || { echo RETURNED_OLD_SYSTEM; return; }
	echo SUCCESS
}
