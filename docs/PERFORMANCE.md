# CR8808 performance record

## Scope and test semantics

Measurements below come from a single CR8808 M81 running the 25.12.2 hwtest1
image on 2026-09-23. Local TCP tests used a WSL host and the router as the two
iperf endpoints. They measure traffic terminating on the router, not routed
traffic:

- **host to router** means the WSL iperf sender transmits to the router.
- **router to host** means the router sends to the WSL receiver.
- These results are not NAT-forwarding, Wi-Fi-forwarding or WireGuard
  throughput limits.

## Local TCP results

| Test | Host to router | Router to host |
|---|---:|---:|
| TCP, one stream | about 635 Mbps | about 501 Mbps |
| TCP, four streams | about 748 Mbps | about 617 Mbps |
| TCP, eight streams | about 736 Mbps | about 642 Mbps |
| Five-minute mixed-load send (router to WSL host; iperf3 reverse mode) | — | 616.84 Mbps average |
| 120-second receive (WSL host to router) | 773.10 Mbps average | — |

The five-minute test also ran ten external WireGuard downloads. The 120-second
receive test completed with all telemetry samples present and concurrent LAN
HTTPS through WireGuard returning successfully. The receive saturation test
reached a minimum MemAvailable of about 7.4 MiB; no OOM event was observed.
That is a measured stress condition, not a safe-memory guarantee.

## Runtime and thermal observations

- Two Cortex-A53 CPUs; one exposed stock OPP at 1.008 GHz.
- The performance governor was already active at that stock frequency; no
  runtime overclock was available or attempted.
- Observed peaks were approximately 60 C CPU, 68 C IPQ5018 and 55 C QCN6122.
- No thermal throttling, OOM, ath11k fatal event or remoteproc restart was
  observed during this bounded test window.
- Linux-visible RAM was about 179.7 MiB. Final idle MemAvailable was about
  26 MiB; the five-minute mixed-load minimum was about 20 MiB.

Absence of an event during this session is not a long-term stability guarantee.

## One-variable A/B results

| Change | Before | Test result | Decision |
|---|---|---|---|
| Packet steering disabled | Default steering: about 740/613 Mbps, host→router / router→host, four-stream control | About 586/442 Mbps, approximately 21% / 28% lower | Roll back; retain default steering |
| Packet steering across all CPUs | Mode 1 control: about 740/613 Mbps | Mode 2: about 739/642 Mbps; repeated result overlapped the returning control | No stable gain; restore mode 1 |
| netdev_budget 300→600 | 300: about 765/641 Mbps | 600 repeated: about 765/641 Mbps | No meaningful gain; restore 300 |
| WireGuard MTU 1370→1380…1420 | 1370 | Larger MTUs passed sampled DF/HTTPS checks but showed no stable throughput advantage | Restore 1370 |
| Software/hardware flow-offload flags | Original flags | No repeatable gain on the tested path | Restore original settings |

The hardware-offload UCI flag did not correspond to working hardware routing
acceleration: the sampled conntrack table had zero HW_OFFLOAD flows. Software
flow entries are not evidence of hardware acceleration. `fq_codel` was retained.
No justified A/B case established a reason to change IRQ affinity, RPS/XPS,
queueing, socket buffers or Wi-Fi channel settings.

The external WireGuard line produced approximately 56–67 Mbps in sampled
downloads, but the remote server and path were uncontrolled. This is line
experience only, not a WireGuard device limit. There was no controlled second
Wi-Fi client or WireGuard iperf server, so no Wi-Fi-forwarding or pure
WireGuard-capacity claim is made.

## Wireless

Both radios operated: IPQ5018 2.4 GHz and QCN6122 5 GHz. A 5 GHz HE80 client
association at 2x2 and a PHY rate around 1200.9 Mbps was observed. PHY rate is
not TCP throughput. **WIFI_FORWARDING_BENCHMARK_NOT_AVAILABLE**: no second
controlled wireless endpoint was available.

## Experimental work and limits

- The stock maximum is 1.008 GHz. No reliable runtime overclock path is
  available. A historical 1.32 GHz attempt was removed and is not validated
  CR8808 support.
- No maintained, complete Linux 6.12/IPQ5018 NSS stack was established for
  this device. `qca_nss_dp` alone is not complete NSS acceleration.
- The ath11k small-buffer/ring limits are retained for the roughly 180 MiB
  Linux-visible memory budget. Larger rings could be evaluated only with a
  controlled Wi-Fi benchmark; current evidence does not show a ring bottleneck.
- No thermal limiting was seen, so the measurements do not justify a cooling
  modification as a performance requirement. Thermal protection remains
  enabled.

No performance change was kept unless repeated results justified it. Details
of the local deployment and private WireGuard failover behavior are maintained
outside this public source tree.
