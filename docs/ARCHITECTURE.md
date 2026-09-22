# Architecture

`OpenWrt -> ImmortalWrt stable -> RainWrt device and safety layer`.

The main line starts from a tagged ImmortalWrt stable release, not by merging
the old device fork. kmiit 24.10 is a hardware-verified behavioral reference.
ByteArray0's 25.12 port supplies the Linux 6.12 DTS/API starting point. RainWrt
reviews each delta and adds strict layout detection around every write path.

The device layer is limited to DTS/DTSI, board-data selection, Ethernet fixes,
image recipes and upgrade guards. Packages come from release-pinned feeds.
User-specific networking is outside this project.
