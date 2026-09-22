# shellcheck shell=ash
# shellcheck disable=SC1091
. /lib/functions.sh

mi_dualboot_current_part() {
	grep -oE 'ubi.mtd=[a-zA-Z0-9_-]*' /proc/cmdline | cut -d= -f2
}

mi_dualboot_target_part() {
	case "$1" in rootfs) echo rootfs_1 ;; rootfs_1) echo rootfs ;; *) return 1 ;; esac
}

mi_dualboot_target_mtdnum() {
	local target mtdnum
	target="$(mi_dualboot_target_part "$1")" || return 1
	mtdnum="$(find_mtd_index "$target")"
	case "$mtdnum" in ''|*[!0-9]*) v "Refusing upgrade: target $target does not exist"; return 1 ;; esac
	[ -c "/dev/mtd$mtdnum" ] || { v "Refusing upgrade: /dev/mtd$mtdnum unavailable"; return 1; }
	echo "$mtdnum"
}

mi_dualboot_check_image() {
	local current
	[ "$(head -c 3 "$1")" = UBI ] || { v "Dual-slot upgrade requires a UBI image"; return 1; }
	current="$(mi_dualboot_current_part)"
	mi_dualboot_target_mtdnum "$current" >/dev/null || return 1
	fw_printenv >/dev/null 2>&1
}

mi_dualboot_do_upgrade() {
	local current mtdnum ubidev
	current="$(mi_dualboot_current_part)"
	mtdnum="$(mi_dualboot_target_mtdnum "$current")" || return 1
	case "$current" in
		rootfs) CI_UBIPART=rootfs_1; local current_slot=0 ;;
		rootfs_1) CI_UBIPART=rootfs; local current_slot=1 ;;
		*) return 1 ;;
	esac
	ubiformat "/dev/mtd$mtdnum" -f "$1" -y || return 1
	sync
	ubiattach --mtdn "$mtdnum" || return 1
	ubidev="$(nand_find_ubi "$CI_UBIPART")"
	[ -n "$(nand_find_volume "$ubidev" kernel)" ] || return 1
	[ -f "$UPGRADE_BACKUP" ] && nand_restore_config "$UPGRADE_BACKUP"
	fw_setenv flag_try_sys1_failed 0 || return 1
	fw_setenv flag_try_sys2_failed 0 || return 1
	fw_setenv flag_last_success "$current_slot" || return 1
	fw_setenv flag_ota_reboot 1 || return 1
	fw_setenv flag_boot_success || return 1
}
