#!/bin/sh
# shellcheck disable=SC1090,SC2317
set -eu

failures=0
script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
subject="${script_dir}/../target/linux/qualcommax/ipq50xx/base-files/lib/upgrade/mi_dualboot.sh"
v() { :; }
find_mtd_index() { case "$1" in rootfs) echo 18 ;; rootfs_1) echo 19 ;; esac; }
sed '/^\. \/lib\/functions\.sh$/d' "$subject" > /tmp/mi-dualboot-test-subject.$$
trap 'rm -f /tmp/mi-dualboot-test-subject.$$' EXIT
. /tmp/mi-dualboot-test-subject.$$

assert_eq() {
	if [ "$1" = "$2" ]; then echo "ok - $3"; else echo "not ok - $3"; failures=$((failures + 1)); fi
}
assert_eq "$(mi_dualboot_target_part rootfs)" rootfs_1 "rootfs targets rootfs_1"
assert_eq "$(mi_dualboot_target_part rootfs_1)" rootfs "rootfs_1 targets rootfs"
if mi_dualboot_target_part invalid >/dev/null 2>&1; then
	echo "not ok - invalid partition rejected"; failures=$((failures + 1))
else
	echo "ok - invalid partition rejected"
fi
if mi_dualboot_target_mtdnum rootfs >/dev/null 2>&1; then
	echo "not ok - non-character target rejected"; failures=$((failures + 1))
else
	echo "ok - non-character target rejected"
fi
exit "$failures"
