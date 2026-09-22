# shellcheck shell=ash
# shellcheck disable=SC1091
. /lib/functions.sh

# Fingerprints for the CR8808 layout and Web-Recovery U-Boot that have been
# verified on hardware. Unknown layouts must never reach a NAND write path.
MI_MIBIB_TABLE_SHA256="b0c9f1a0239bd150e121063278d123b30e7697a6959ea4543cce8e83aa47ca54"
MI_SINGLE_APPSBL_SHA256="a92f08878499bb697e67cfb5f597bb5757e48b4846f4f250fbc612ea166ad4f3"

mi_layout_proc_mtd() { echo "${MI_PROC_MTD:-/proc/mtd}"; }
mi_layout_cmdline() { echo "${MI_PROC_CMDLINE:-/proc/cmdline}"; }
mi_layout_mtddev() { echo "${MI_MTD_DEV_PREFIX:-/dev/mtd}"; }

mi_layout_mtd_line() {
	awk -v needle="\"$1\"" '$4 == needle { print; found=1 } END { exit !found }' \
		"$(mi_layout_proc_mtd)"
}

mi_layout_mtd_size() { mi_layout_mtd_line "$1" | awk '{ print $2 }'; }
mi_layout_mtd_index() {
	mi_layout_mtd_line "$1" | sed -n 's/^mtd\([0-9][0-9]*\):.*/\1/p'
}

mi_layout_mtd_device_ok() {
	local path
	path="$(mi_layout_mtddev)$1"
	[ -c "$path" ] || { [ "${MI_TEST_ALLOW_REGULAR_MTD:-0}" = 1 ] && [ -f "$path" ]; }
}

mi_layout_mibib_fingerprint() {
	local index
	index="$(mi_layout_mtd_index '0:MIBIB')"
	[ -n "$index" ] || return 1
	dd if="$(mi_layout_mtddev)${index}" bs=1 skip=2048 count=632 2>/dev/null |
		sha256sum | awk '{ print $1 }'
}

mi_layout_appsbl_fingerprint() {
	local index
	index="$(mi_layout_mtd_index '0:APPSBL')"
	[ -n "$index" ] || return 1
	sha256sum "$(mi_layout_mtddev)${index}" 2>/dev/null | awk '{ print $1 }'
}

mi_layout_board_supported() {
	case "$1" in
		redmi,ax3000|xiaomi,cr880x-m81) return 0 ;;
		*) return 1 ;;
	esac
}

mi_layout_is_single() {
	[ "$(mi_layout_mtd_index rootfs)" = 18 ] || return 1
	[ "$(mi_layout_mtd_size rootfs)" = 07480000 ] || return 1
	mi_layout_mtd_device_ok 18 || return 1
	! mi_layout_mtd_line rootfs_1 >/dev/null 2>&1 || return 1
	grep -Eq '(^|[[:space:]])ubi\.mtd=rootfs([[:space:]]|$)' "$(mi_layout_cmdline)" || return 1
	[ "$(mi_layout_mibib_fingerprint)" = "$MI_MIBIB_TABLE_SHA256" ] || return 1
	[ "$(mi_layout_mtd_index '0:APPSBL')" = 12 ] || return 1
	[ "$(mi_layout_appsbl_fingerprint)" = "$MI_SINGLE_APPSBL_SHA256" ] || return 1
	[ "$(fw_printenv -n bootcmd 2>/dev/null)" = bootmiwifi ] || return 1
}

mi_layout_is_legacy_dual() {
	local current
	current="$(mi_dualboot_current_part)"
	case "$current" in rootfs|rootfs_1) ;; *) return 1 ;; esac
	[ "$(mi_layout_mtd_size rootfs)" = 02400000 ] || return 1
	[ "$(mi_layout_mtd_size rootfs_1)" = 02400000 ] || return 1
	[ "$(mi_layout_mibib_fingerprint)" = "$MI_MIBIB_TABLE_SHA256" ] || return 1
	mi_dualboot_target_mtdnum "$current" >/dev/null
}

mi_layout_detect() {
	if mi_layout_is_single; then
		echo rainwrt-single-slot
	elif mi_layout_is_legacy_dual; then
		echo legacy-dual-slot
	else
		return 1
	fi
}

mi_single_check_image() {
	[ "$(mi_layout_detect)" = rainwrt-single-slot ] || {
		v "Refusing single-slot upgrade: layout fingerprint changed"
		return 1
	}
	nand_do_platform_check "$1" "$2"
}

mi_single_do_upgrade() {
	[ "$(mi_layout_detect)" = rainwrt-single-slot ] || {
		v "Refusing single-slot upgrade: layout fingerprint changed before write"
		return 1
	}
	# shellcheck disable=SC2034
	CI_UBIPART=rootfs
	# shellcheck disable=SC2034
	CI_KERNPART=kernel
	# shellcheck disable=SC2034
	CI_ROOTPART=rootfs
	nand_do_upgrade "$1"
}
