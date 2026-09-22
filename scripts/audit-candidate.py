#!/usr/bin/env python3
"""Offline artifact/ABI/feed audit; never connects to or modifies a router."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=pathlib.Path, required=True)
    p.add_argument('--build-root', type=pathlib.Path, required=True)
    args = p.parse_args()
    out, build = args.candidate.resolve(), args.build_root.resolve()
    expected = json.loads((out / 'candidate.json').read_text())
    root = out / 'static-inspection/rootfs'
    apk = str(build / 'staging_dir/host/bin/apk')
    def run(argv):
        return subprocess.run(argv, check=True, capture_output=True).stdout
    for name, digest in expected['files'].items():
        with (out / name).open('rb') as stream:
            require(hashlib.file_digest(stream, 'sha256').hexdigest() == digest, 'file checksum mismatch')
    packages = ['kmod-wireguard', 'wireguard-tools', 'luci-proto-wireguard', 'wpad-openssl', 'luci']
    info_args = [apk, '--root', str(root), '--no-network', 'info', '-e']
    run(info_args + packages)
    missing = subprocess.run(info_args + ['kmod-wireguard', 'rainwrt-negative-nonexistent'], capture_output=True)
    require(missing.returncode != 0, 'APK existence query is fail-open')
    module_count = 0
    for module in (root / 'lib/modules' / expected['kernel']).glob('*.ko*'):
        abi = run(['modinfo', '-F', 'vermagic', str(module)]).decode().split()[0]
        require(abi == expected['kernel'], 'mixed kernel module ABI')
        module_count += 1
    require(module_count > 10, 'missing kernel modules')
    indexes = sorted((out / 'packages').rglob('packages.adb'))
    keys = out / 'packages/keys'
    for index in indexes:
        run([apk, '--keys-dir', str(keys), 'verify', str(index)])
    # OpenWrt signs indexes, not each APK. APK fetch verifies content through
    # trusted indexes. No --allow-untrusted/force flags, no remote URLs.
    with tempfile.TemporaryDirectory(prefix='rainwrt-apk-audit-') as directory:
        argv = [apk, '--keys-dir', str(keys), '--arch', 'aarch64_cortex-a53', '--no-network', '--no-cache']
        for index in indexes:
            argv += ['-X', str(index)]
        run(argv + ['fetch', '-R', '-o', directory] + packages)
        fetched = len(list(pathlib.Path(directory).glob('*.apk')))
        require(fetched >= len(packages), 'incomplete dependency closure')
    board_hashes = {}
    for chip, suffix in [('IPQ5018', 'ipq5018'), ('QCN6122', 'qcn6122')]:
        original = build / ('package/firmware/ipq-wifi/src/board-redmi_ax3000.' + suffix)
        actual = root / ('lib/firmware/ath11k/' + chip + '/hw1.0/board-2.bin')
        require(original.read_bytes() == actual.read_bytes(), 'installed BDF mismatch')
        board_hashes[chip] = hashlib.sha256(actual.read_bytes()).hexdigest()
    cmd = build / ('build_dir/target-aarch64_cortex-a53_musl/linux-qualcommax_ipq50xx/'
                   'mac80211-regular/backports-6.18.39/drivers/net/wireless/ath/ath11k/.core.o.cmd')
    require('-DCONFIG_ATH11K_SMALLBUFFERS' in cmd.read_text(), 'low-memory flag not compiled')
    print(json.dumps({'status': 'PASS', 'kernel': expected['kernel'], 'modules_checked': module_count,
                      'signed_indexes': len(indexes), 'APK_dependency_closure': fetched,
                      'APK_negative_query': 'PASS', 'BDF': board_hashes,
                      'smallbuffers_compile_flag': 'PASS', 'hardware': 'NOT_RUN'}, indent=2))


if __name__ == '__main__':
    main()
