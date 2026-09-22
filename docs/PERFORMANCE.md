# Performance evidence and boundaries

Read-only reference evidence: two Cortex-A53 CPUs; ARM64 AES/PMULL/SHA/ASIMD;
184956 KiB Linux-visible RAM; no swap. Available RAM varied substantially under
normal use. `nss-dp-gmac` interrupts identify the Ethernet datapath, **not** proof
of NSS routing/ath11k offload. Several queues/interrupts concentrate on CPU0;
that is a measurement, not justification for a blind affinity mask.

Safe default changes: restore the previously working ath11k low-memory budget
(mode 2, 4 vdevs/32 peers, bounded rings). This is compatibility work, not a
throughput claim. No overclock, thermal bypass, IRQ/RPS/XPS override, conntrack
increase, zram or network sysctl bundle is added.

`scripts/performance-audit.sh` reads CPU/frequency/temperature, memory, IRQs,
softirqs, queue masks, qdisc, supported radio capabilities and UBI/df. Missing
tools are reported as unavailable. It generates no traffic and changes no
settings. Existing firmware and candidate measurements must be kept separate.

Optional future experiments: one-variable packet steering, software flow
offload (check SQM/accounting compatibility), and measured WireGuard MTU.
Start with wired LAN-to-LAN iperf, then a separate LAN-to-WAN forwarding test,
then Wi-Fi and WireGuard tests. Host-to-router iperf is not NAT throughput.
No numeric performance improvement is claimed without paired measurements.

NSS status: QSDK IPQ5018 firmware existence does not provide an upstream Linux
6.12 NSS driver/ath11k integration. ByteArray0's port does not establish such
support. Unrelated IPQ807x/IPQ6018 NSS projects are not IPQ5018 evidence.
No aggressive NSS acceleration is enabled in this candidate.
