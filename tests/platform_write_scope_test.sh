#!/bin/sh
# Only mocked primitives; never sources router runtime files or touches devices.
# shellcheck disable=SC1090,SC1091,SC2034,SC2317
set -eu
root="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT HUP INT TERM
subject="$root/target/linux/qualcommax/ipq50xx/base-files/lib/upgrade/platform.sh"
sed '/^\. \/lib\//d' "$subject" > "$fixture/platform.sh"
. "$fixture/platform.sh"
board_name() { echo "$test_board"; }
mi_layout_board_supported() { [ "$1" = redmi,ax3000 ]; }
mi_layout_detect() { [ "$test_mode" = rainwrt-single-slot ] && echo "$test_mode"; }
mi_single_check_image() { echo CHECK; }
mi_single_do_upgrade() { echo SINGLE_SLOT_PRIMITIVE; }
fw_setenv() { echo FORBIDDEN >&2; exit 91; }
mtd() { echo FORBIDDEN >&2; exit 92; }
ubiformat() { echo FORBIDDEN >&2; exit 93; }
v() { :; }
reject() { if "$@"; then echo 'FAIL: write path accepted' >&2; exit 1; fi; }
test_board=redmi,ax3000
test_mode=rainwrt-single-slot
[ "$(platform_check_image fixture)" = CHECK ]
[ "$(platform_do_upgrade fixture)" = SINGLE_SLOT_PRIMITIVE ]
test_mode=legacy-dual-slot
reject platform_check_image fixture
reject platform_do_upgrade fixture
test_board=xiaomi,cr880x-m79-v1
reject platform_check_image fixture
reject platform_do_upgrade fixture
grep -Fq '/lib/upgrade/*.sh' "$root/package/base-files/files/lib/upgrade/stage2"
for helper in mi_layout.sh mi_dualboot.sh platform.sh; do
    test -s "$root/target/linux/qualcommax/ipq50xx/base-files/lib/upgrade/$helper"
done
printf 'PASS: CR8808 routes only to guarded single-slot; dual/M79 reject; stage2 includes helpers\n'
