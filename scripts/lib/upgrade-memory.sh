#!/bin/sh
# Read-only numeric probes. Never source or execute upgrade functions.
memory_paths() {
    if [ "$1" = handoff ]; then
        binaries=upgraded
    else
        binaries='busybox ash sh mount umount pivot_root mount_root reboot sync kill sleep md5sum hexdump cat zcat dd tar gzip ls basename find cp mv rm mkdir rmdir mknod touch chmod printf wc grep awk sed cut sort tail mtd partx losetup mkfs.ext4 nandwrite flash_erase ubiupdatevol ubiattach ubiblock ubiformat ubidetach ubirsvol ubirmvol ubimkvol snapshot snapshot_tool date logger fw_printenv fw_setenv fwtool dumpimage head seq sha256sum upgraded ubus'
    fi
    for b in $binaries; do
        p=$(command -v "$b" 2>/dev/null || true)
        [ -f "$p" ] || continue
        readlink -f "$p"
        ldd "$p" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i ~ /^\//) print $i}' || true
    done
    if [ "$1" = stage2 ]; then
        find /lib/upgrade /lib/functions -type f
        find /lib -maxdepth 1 -name '*.sh'
        printf '%s\n' /usr/share/libubox/jshn.sh /etc/fw_env.config /etc/resolv.conf /var/lock/fw_printenv.lock
    fi
}
memory_size() {
    memory_paths "$1" | while IFS= read -r p; do
        [ ! -f "$p" ] || readlink -f "$p"
    done | sort -u | while IFS= read -r p; do wc -c < "$p"; done |
        awk '{n++; raw+=$1; pages+=int(($1+4095)/4096)*4} END {printf "%d,%d,%d",raw,pages,n}'
}
memory_profile() {
    set -eu
    h=$(memory_size handoff)
    r=$(memory_size stage2)
    printf '{"handoff":[%s],"stage2":[%s]}\n' "$h" "$r"
}
memory_sample() {
    set -eu
    # Subtract PID1 and this observer's ancestry from global unique AnonPages.
    # Their RSS may share pages: over-subtraction is deliberately conservative.
    p=$$
    observer=0
    while [ "$p" -ge 1 ]; do
        a=$(awk '/^RssAnon:/ {print $2}' "/proc/$p/status")
        case "$a" in ''|*[!0-9]*) return 1;; esac
        observer=$((observer + a))
        [ "$p" -ne 1 ] || break
        p=$(awk '/^PPid:/ {print $2}' "/proc/$p/status")
        [ "$p" -gt 0 ] || break
    done
    tmp=$(df -Pk /tmp | awk 'NR==2 {print $4}')
    awk -v tmp="$tmp" -v observer="$observer" '
      /^MemAvailable:/ {mem=$2; fields++}
      /^AnonPages:/ {anon=$2; fields++}
      /^Unevictable:/ {locked+=$2; fields++}
      /^Mlocked:/ {locked+=$2; fields++}
      /^SwapTotal:/ {swap=$2; fields++}
      END {if(fields!=5 || tmp=="" || mem<=0) exit 1; printf "{\"mem_kib\":%d,\"tmp_kib\":%d,\"anon_kib\":%d,\"observer_anon_kib\":%d,\"locked_kib\":%d,\"swap_kib\":%d}\n",mem,tmp,anon,observer,locked,swap}
    ' /proc/meminfo
}
memory_pre_handoff() {
    set -eu
    ramfs_kib=$1
    handoff_kib=$2
    config_kib=$3
    sample=$(memory_sample)
    mem=$(printf '%s' "$sample" | jsonfilter -e '@.mem_kib')
    tmp=$(printf '%s' "$sample" | jsonfilter -e '@.tmp_kib')
    anon=$(printf '%s' "$sample" | jsonfilter -e '@.anon_kib')
    observer=$(printf '%s' "$sample" | jsonfilter -e '@.observer_anon_kib')
    locked=$(printf '%s' "$sample" | jsonfilter -e '@.locked_kib')
    swap=$(printf '%s' "$sample" | jsonfilter -e '@.swap_kib')
    credit=0
    if [ "$locked" -eq 0 ] && [ "$swap" -eq 0 ] && [ "$anon" -gt "$observer" ]; then
        credit=$((anon - observer))
        [ "$credit" -le "$ramfs_kib" ] || credit=$ramfs_kib
    fi
    physical=$((ramfs_kib + 8192 + config_kib - credit))
    running=$((handoff_kib + 8192 + config_kib))
    [ "$physical" -ge "$running" ] || physical=$running
    capacity=$((2 * ramfs_kib + config_kib))
    printf 'PRE_HANDOFF_MEMORY mem_kib=%s tmp_kib=%s physical_required_kib=%s tmp_required_kib=%s\n' "$mem" "$tmp" "$physical" "$capacity"
    [ "$mem" -ge "$physical" ] && [ "$tmp" -ge "$capacity" ]
}
