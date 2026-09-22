#!/bin/sh
# shellcheck disable=SC1007,SC1090,SC2034,SC2317
set -eu

failures=0
script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
source_dir="${script_dir}/../target/linux/qualcommax/ipq50xx/base-files/lib/upgrade"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture" /tmp/mi-layout-subject.$$ /tmp/mi-dual-subject.$$' EXIT

v() { :; }
fw_printenv() { [ "$1" = -n ] && [ "$2" = bootcmd ] && echo bootmiwifi; }
find_mtd_index() { mi_layout_mtd_index "$1"; }

sed '/^\. \/lib\/functions\.sh$/d' "$source_dir/mi_dualboot.sh" > /tmp/mi-dual-subject.$$
. /tmp/mi-dual-subject.$$
sed '/^\. \/lib\/functions\.sh$/d' "$source_dir/mi_layout.sh" > /tmp/mi-layout-subject.$$
. /tmp/mi-layout-subject.$$

assert_mode() {
	expected="$1"; name="$2"
	if actual="$(mi_layout_detect 2>/dev/null)" && [ "$actual" = "$expected" ]; then
		echo "ok - $name"
	else
		echo "not ok - $name"
		failures=$((failures + 1))
	fi
}

assert_rejected() {
	if mi_layout_detect >/dev/null 2>&1; then
		echo "not ok - $1"; failures=$((failures + 1))
	else
		echo "ok - $1"
	fi
}

MI_PROC_MTD="$fixture/proc-mtd"
MI_PROC_CMDLINE="$fixture/cmdline"
MI_MTD_DEV_PREFIX="$fixture/mtd"
MI_TEST_ALLOW_REGULAR_MTD=1
export MI_PROC_MTD MI_PROC_CMDLINE MI_MTD_DEV_PREFIX MI_TEST_ALLOW_REGULAR_MTD

printf 'dev: size erasesize name\nmtd1: 00080000 00020000 "0:MIBIB"\nmtd12: 00140000 00020000 "0:APPSBL"\nmtd18: 07480000 00020000 "rootfs"\n' > "$MI_PROC_MTD"
printf 'console=ttyMSM0,115200n8 ubi.mtd=rootfs root=mtd:ubi_rootfs\n' > "$MI_PROC_CMDLINE"
dd if=/dev/zero of="$fixture/mtd1" bs=1 count=2676 status=none
printf fixture-mibib-table | dd of="$fixture/mtd1" bs=1 seek=2048 conv=notrunc status=none
: > "$fixture/mtd18"
printf fixture-appsbl > "$fixture/mtd12"
MI_MIBIB_TABLE_SHA256="$(dd if="$fixture/mtd1" bs=1 skip=2048 count=632 2>/dev/null | sha256sum | awk '{print $1}')"
MI_SINGLE_APPSBL_SHA256="$(sha256sum "$fixture/mtd12" | awk '{print $1}')"

assert_mode rainwrt-single-slot "known merged layout selects single-slot path"
sed -i 's/07480000/07460000/' "$MI_PROC_MTD"
assert_rejected "single-slot size mismatch fails closed"
sed -i 's/07460000/07480000/' "$MI_PROC_MTD"
printf 'mtd19: 02400000 00020000 "rootfs_1"\n' >> "$MI_PROC_MTD"
assert_rejected "unexpected rootfs_1 fails closed"
sed -i '$d' "$MI_PROC_MTD"
printf changed-appsbl > "$fixture/mtd12"
assert_rejected "unknown bootloader fails closed"

exit "$failures"
