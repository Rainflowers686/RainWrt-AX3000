# Architecture

OpenWrt → ImmortalWrt stable → RainWrt.

RainWrt follows ImmortalWrt stable rather than treating the retired kmiit
24.10 fork as its permanent base. The tested 24.10 image remains a known-good
behavioral reference. The current line forward-ports only the device support
and compatibility changes needed for the maintained 25.12.2 base.

The downstream layer is limited to CR880X DTS/DTSI, device and board-data
selection, Ethernet compatibility, image recipes, configuration ABI migration
and fail-closed upgrade checks. Every imported change keeps its provenance;
RainWrt-specific work is separate. Package feeds are pinned to the matching
ImmortalWrt release.

The CR8808 M81 validation applies to one device with a custom Web-Recovery
bootloader and runtime merged-rootfs FDT. The upgrade detector does not infer
that map from the model name alone. See CR8808_FLASH_LAYOUT.md,
UPGRADE_SAFETY.md and HARDWARE_VALIDATION.md.

Private deployment configuration is outside RainWrt. Standard sysupgrade
configuration preservation is generic and does not add support for any
institution-specific service or VPN peer.
