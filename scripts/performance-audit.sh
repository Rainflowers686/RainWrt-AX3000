#!/bin/sh
# Run on the router, or stream over SSH. Read-only; no traffic generation.
set -u
show() {
    printf '\n[%s]\n' "$1"
    shift
    "$@" 2>/dev/null || printf 'UNAVAILABLE\n'
}
show cpu sh -c "grep -E 'processor|BogoMIPS|Features' /proc/cpuinfo"
show memory cat /proc/meminfo
show load cat /proc/loadavg
show interrupts sh -c "sed -E 's/([0-9a-f]{2}:){5}[0-9a-f]{2}/[MAC]/g' /proc/interrupts"
show softirq cat /proc/softirqs
for f in /sys/devices/system/cpu/cpufreq/policy*/scaling_governor /sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq /sys/class/thermal/thermal_zone*/temp /sys/class/net/*/queues/rx-*/rps_cpus /sys/class/net/*/queues/tx-*/xps_cpus; do
    [ ! -f "$f" ] || show "$f" cat "$f"
done
show qdisc tc -s qdisc show
for p in wan lan1 lan2 lan3 eth0 eth1; do
    [ -e "/sys/class/net/$p" ] || continue
    show "$p link" sh -c "ethtool '$p' | grep -E 'Speed:|Duplex:|Link detected:'"
    show "$p offload" ethtool -k "$p"
done
show wireless-capabilities sh -c "iw phy | grep -E 'Wiphy|Band |MHz \\[|HE Iftypes|HE PHY|VHT Capabilities|HT20|HT40|NSS'"
show ubi ubinfo -a
show rootfs df -k /rom /overlay /tmp
printf '\nNO_BENCHMARK_RUN: host-to-router is not NAT/Wi-Fi/WireGuard forwarding throughput.\n'
