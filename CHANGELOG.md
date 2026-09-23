# Changelog

## 25.12.2 hardware-validated development line — 2026-09-22/23

- Forward-ported the Redmi AX3000 / CR880X device layer to ImmortalWrt 25.12.2
  and Linux 6.12.103.
- Completed static image/feed checks and a real NAND sysupgrade on one CR8808
  M81.
- Validated first boot, normal reboot, Ethernet, IPv4/IPv6, IPQ5018 2.4 GHz,
  QCN6122 5 GHz, ath11k, APK and WireGuard capability.
- Fixed the exact 24.10-to-25.12 QCN6122 wireless path migration and verified
  both radios and persistence across reboot.
- Validated generic configuration and custom-service-state migration.
- Completed bounded local TCP, WireGuard line-experience, thermal and memory
  observations; no unproven performance tweak was retained.
- Public binary release remains blocked while board-data redistribution terms
  are unresolved. This is not a stable-release announcement.

## 24.10 known-good reference — 2026-09-22

- Preserved the kmiit-derived ImmortalWrt 24.10 hardware-verified build as a
  reference baseline.
- Its source, image identity and tested functions are recorded in
  docs/KNOWN_GOOD_24.10.md.
