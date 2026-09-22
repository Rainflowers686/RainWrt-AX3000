#!/bin/sh
# Read-only, sanitized machine evidence. No UCI values, SSIDs, IP addresses,
# credentials, service contents or environment dump are emitted.
set -eu
command -v jq >/dev/null
board="$(cat /tmp/sysinfo/board_name)"
kernel="$(uname -r)"
identity='{}'
if [ -f /etc/rainwrt-release ]; then
    # jq's minimal build has no regex engine. Exact identity is checked on host.
    identity="$(jq -Rn '[inputs | split("=") | {key:.[0],value:(.[1] | .[1:-1])}] | from_entries' < /etc/rainwrt-release)"
fi
release="$(ubus call system board | jq '{release: .release.version, revision: .release.revision, target: .release.target}')"
mtd="$(cat /proc/mtd)"
mibib="$(dd if=/dev/mtd1 bs=1 skip=2048 count=632 2>/dev/null | sha256sum | cut -d' ' -f1)"
appsbl="$(sha256sum /dev/mtd12 | cut -d' ' -f1)"
bootcmd="$(fw_printenv -n bootcmd)"
char=false; [ ! -c /dev/mtd18 ] || char=true
cmdline=false; grep -Eq '(^| )ubi\.mtd=rootfs( |$)' /proc/cmdline && cmdline=true
offset="$(cat /sys/class/mtd/mtd18/offset)"
mem="$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)"
tmp="$(df -Pk /tmp | awk 'NR==2 {print $4}')"
boot_id="$(cat /proc/sys/kernel/random/boot_id)"
uptime="$(cut -d' ' -f1 /proc/uptime)"
load="$(cut -d' ' -f1-3 /proc/loadavg)"
ubi=''; for f in /sys/class/ubi/ubi0_*/name; do [ ! -f "$f" ] || ubi="$ubi $(cat "$f")"; done
ubi_mtd="$(cat /sys/class/ubi/ubi0/mtd_num 2>/dev/null || echo -1)"
mounts="$(awk '$2=="/" || $2=="/rom" || $2=="/overlay" {print $2 " " $3 " " $1}' /proc/mounts)"
fatal=false
if dmesg | grep -Eiq '(ath11k.*(firmware crashed|failed to|fatal|timed out)|remoteproc.*crash|UBI error|UBIFS error|ubi.*attach.*fail|I/O error.*mtd)'; then fatal=true; fi
phy=''; for f in /sys/class/ieee80211/phy*/device; do [ ! -e "$f" ] || phy="$phy $(readlink -f "$f")"; done
rproc=''; for f in /sys/class/remoteproc/remoteproc*/state; do [ ! -f "$f" ] || rproc="$rproc $(cat "$f")"; done
wifi="$(ubus call network.wireless status | jq '[to_entries[] | {name:.key, up:.value.up, disabled:(.value.disabled // false), pending:(.value.pending // false), retry_setup_failed:(.value.retry_setup_failed // false), path:(.value.config.path // ""), band:(.value.config.band // "")}]')"
wifi_devices="$(ubus call uci get '{"config":"wireless"}' | jq '[.values | to_entries[] | select(.value[".type"] == "wifi-device") | {name:.key,path:(.value.path // ""),band:(.value.band // ""),disabled:(.value.disabled == "1")}]')"
aps="$(
    for f in /sys/class/net/*/phy80211; do
        [ -e "$f" ] || continue
        iface="${f%/phy80211}"; iface="${iface##*/}"
        [ "$(iw dev "$iface" info | awk '$1=="type" {print $2}')" = AP ] || continue
        path="$(readlink -f "$f/device")"; path="${path#/sys/devices/}"
        up=false; flags="$(cat "/sys/class/net/$iface/flags")"
        [ "$((flags & 1))" -eq 0 ] || up=true
        enabled="$(ubus call "hostapd.$iface" get_status 2>/dev/null | jq '.status == "ENABLED"')"
        jq -n --arg name "$iface" --arg path "$path" --argjson up "$up" --argjson enabled "${enabled:-false}" \
          '{name:$name,path:$path,up:$up,hostapd_enabled:$enabled}'
    done | jq -s .
)"
bands="$(iw phy | awk '/MHz \[/ {if ($2>=2400 && $2<2500) a=1; if ($2>=5000 && $2<6000) b=1} END {printf "%d %d",a,b}')"
bdf="$(dmesg | sed -n 's/.*board_id \(0x[0-9a-f]*\).*/\1/p' | sort -u | tr '\n' ' ')"
ports=''; for p in lan1 lan2 lan3 wan br-lan; do [ ! -e "/sys/class/net/$p" ] || ports="$ports $p"; done
carrier=false; [ "$(cat /sys/class/net/br-lan/carrier 2>/dev/null || echo 0)" != 1 ] || carrier=true
wg=false; command -v wg >/dev/null && wg --version >/dev/null && wg=true
wg_abi="$(modinfo wireguard 2>/dev/null | sed -n 's/^vermagic:[[:space:]]*//p' | cut -d' ' -f1)"
apk=false
if command -v apk >/dev/null && apk info -e kmod-wireguard wireguard-tools luci-proto-wireguard >/dev/null 2>&1; then apk=true; fi
ipv4=false; ip -4 route show default | grep -q . && ipv4=true
ipv6=false; ip -6 route show default | grep -q . && ipv6=true
resolver=false; grep -q '^nameserver ' /tmp/resolv.conf.d/resolv.conf.auto && resolver=true
# Upper bound: all stage2 binaries plus their shared-library closure and scripts.
stage2_kib="$(
    for b in busybox ash sh mount umount pivot_root mount_root reboot sync kill sleep md5sum hexdump cat zcat dd tar gzip ls basename find cp mv rm mkdir rmdir mknod touch chmod printf wc grep awk sed cut sort tail mtd partx losetup mkfs.ext4 nandwrite flash_erase ubiupdatevol ubiattach ubiblock ubiformat ubidetach ubirsvol ubirmvol ubimkvol snapshot snapshot_tool date logger fw_printenv fwtool dumpimage sha256sum upgraded ubus; do
        p="$(command -v "$b" 2>/dev/null || true)"
        [ -n "$p" ] || continue
        readlink -f "$p"
        ldd "$p" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i ~ /^\//) print $i}' || true
    done
    find /lib/upgrade /lib/functions -type f
    find /lib -maxdepth 1 -name '*.sh'
    echo /usr/share/libubox/jshn.sh
    echo /etc/fw_env.config
    )"
stage2_kib="$(printf '%s\n' "$stage2_kib" | sort -u | while IFS= read -r p; do [ ! -f "$p" ] || wc -c < "$p"; done | awk '{s+=$1} END {print int(s/1024)+1}')"
[ "$stage2_kib" -ge 512 ] || { echo 'Stage2 measurement invalid' >&2; exit 1; }
jq -n --arg board "$board" --arg kernel "$kernel" --argjson identity "$identity" --argjson release "$release" \
 --arg mtd "$mtd" --arg mibib "$mibib" --arg appsbl "$appsbl" --arg bootcmd "$bootcmd" \
 --argjson char "$char" --argjson cmdline "$cmdline" --argjson offset "$offset" \
 --argjson mem "$mem" --argjson tmp "$tmp" --arg boot_id "$boot_id" --argjson uptime "$uptime" --arg load "$load" \
 --arg ubi "$ubi" --argjson ubi_mtd "$ubi_mtd" --arg mounts "$mounts" --argjson fatal "$fatal" \
 --arg phy "$phy" --arg rproc "$rproc" --argjson wifi "$wifi" --argjson wifi_devices "$wifi_devices" --argjson aps "$aps" --arg bands "$bands" --arg bdf "$bdf" \
 --arg ports "$ports" --argjson carrier "$carrier" --argjson wg "$wg" --arg wg_abi "$wg_abi" --argjson apk "$apk" \
 --argjson ipv4 "$ipv4" --argjson ipv6 "$ipv6" --argjson resolver "$resolver" --argjson stage2 "$stage2_kib" \
 '{board:$board,kernel:$kernel,identity:$identity,release:$release,mtd:$mtd,mibib:$mibib,appsbl:$appsbl,bootcmd:$bootcmd,
 char:$char,cmdline:$cmdline,offset:$offset,mem_kib:$mem,tmp_kib:$tmp,boot_id:$boot_id,uptime:$uptime,load:$load,
 ubi:$ubi,ubi_mtd:$ubi_mtd,mounts:$mounts,fatal:$fatal,phy:$phy,rproc:$rproc,wifi:$wifi,wifi_devices:$wifi_devices,aps:$aps,bands:$bands,bdf:$bdf,
 ports:$ports,carrier:$carrier,wg:$wg,wg_abi:$wg_abi,apk:$apk,ipv4:$ipv4,ipv6:$ipv6,resolver:$resolver,stage2_kib:$stage2}'
