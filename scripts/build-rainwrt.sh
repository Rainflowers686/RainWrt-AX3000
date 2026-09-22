#!/bin/sh
set -eu

root="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
jobs="${JOBS:-$(nproc)}"
# OpenWrt uses `find -execdir` while assembling the rootfs. GNU find refuses
# that operation when PATH contains relative/empty entries; Windows paths with
# spaces inherited by some WSL launchers can be split into such entries by
# upstream make recipes. Build with Linux tool paths only.
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PATH
cd "$root"

./scripts/feeds update -a
./scripts/feeds install -a
python3 scripts/prepare-rainwrt-build.py
cp configs/redmi_ax3000_baseline-wg.config .config
make defconfig
make -j"$jobs" download
make -j"$jobs" world

target_dir="$root/bin/targets/qualcommax/ipq50xx"
[ -d "$target_dir" ] || { echo "missing target output" >&2; exit 1; }
checksum_tmp="$(mktemp)"
trap 'rm -f "$checksum_tmp"' EXIT HUP INT TERM
(cd "$target_dir" &&
	find . -maxdepth 1 -type f ! -name SHA256SUMS -print0 |
		LC_ALL=C sort -z | xargs -0 sha256sum) > "$checksum_tmp"
mv "$checksum_tmp" "$target_dir/SHA256SUMS"
trap - EXIT HUP INT TERM
