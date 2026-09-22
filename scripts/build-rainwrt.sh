#!/bin/sh
set -eu

root="$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)"
jobs="${JOBS:-$(nproc)}"
cd "$root"

./scripts/feeds update -a
./scripts/feeds install -a
cp configs/redmi_ax3000_baseline-wg.config .config
make defconfig
make -j"$jobs" download
make -j"$jobs" world

target_dir="$root/bin/targets/qualcommax/ipq50xx"
[ -d "$target_dir" ] || { echo "missing target output" >&2; exit 1; }
(cd "$target_dir" && sha256sum -- * > SHA256SUMS)
