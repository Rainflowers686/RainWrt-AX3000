#!/usr/bin/env python3
"""Generate ignored build inputs from an immutable, clean source revision."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def main():
    if git('status', '--porcelain', '--untracked-files=normal'):
        raise SystemExit('Refusing to stamp a dirty source tree')
    source = git('rev-parse', 'HEAD')
    upstream = '4fc16f2985a358bd43bb522e43f05395fcbd6ed5'
    subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', upstream, source], check=True)
    feeds = (ROOT / 'feeds.conf.default').read_text()
    for line in feeds.splitlines():
        if not line or line.startswith('#'):
            continue
        name, revision = line.split()[1], line.rsplit('^', 1)[-1]
        actual = subprocess.check_output(['git', '-C', str(ROOT / 'feeds' / name), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != revision:
            raise SystemExit('Feed revision mismatch: ' + name)
    config = ROOT / 'configs/redmi_ax3000_baseline-wg.config'
    digest = hashlib.sha256(config.read_bytes() + feeds.encode()).hexdigest()
    identity = {
        'RAINWRT_VERSION': '25.12.2-hwtest1',
        'RAINWRT_BUILD_ID': '25.12.2-hwtest1-' + source[:12] + '-' + digest[:12],
        'RAINWRT_SOURCE_REVISION': source,
        'RAINWRT_UPSTREAM_VERSION': '25.12.2',
        'RAINWRT_UPSTREAM_REVISION': upstream,
        'RAINWRT_TARGET': 'qualcommax/ipq50xx',
        'RAINWRT_PROFILE': 'redmi_ax3000',
        'RAINWRT_BUILD_STATUS': 'hardware-test-candidate',
    }
    output = ROOT / 'files/etc/rainwrt-release'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(f"{k}='{v}'\n" for k, v in identity.items()))
    # A downstream kernel must not use official core packages of another ABI.
    # All signed APK indexes/packages are retained alongside the candidate.
    repo = ROOT / 'files/etc/apk/repositories.d/distfeeds.list'
    repo.parent.mkdir(parents=True, exist_ok=True)
    repo.write_text('# RainWrt hardware-test candidate: no hosted repository yet.\n'
                    '# Use the signed, ABI-matched archived APK feed only.\n'
                    '# Do not add official core feeds or --allow-untrusted.\n')
    out = ROOT / 'rainwrt-build-identity.json'
    out.write_text(json.dumps(identity, indent=2) + '\n')
    print(identity['RAINWRT_BUILD_ID'])


if __name__ == '__main__':
    main()
