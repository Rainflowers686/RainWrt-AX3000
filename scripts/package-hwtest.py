#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Package an already built candidate, independently checking tar/UBI contents.

UBI structures/CRC follow Linux drivers/mtd/ubi/ubi-media.h; no NAND operations.
Does not register a trust anchor or authorize a hardware write.
"""
import argparse
import hashlib
import json
import pathlib
import re
import shutil
import struct
import subprocess
import tarfile
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFIX = 'immortalwrt-qualcommax-ipq50xx-redmi_ax3000'


def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def require(condition, text):
    if not condition:
        raise RuntimeError(text)


def inspect_ubi(path, expected):
    data = path.read_bytes()
    require(len(data) % 0x20000 == 0, 'unaligned UBI')
    volumes, tables, sequence = {}, [], set()
    for offset in range(0, len(data), 0x20000):
        block = data[offset:offset + 0x20000]
        require(block[:4] == b'UBI#', 'invalid EC magic')
        require(struct.unpack_from('>I', block, 60)[0] == (~zlib.crc32(block[:60]) & 0xffffffff), 'EC CRC')
        vid, payload, seq = struct.unpack_from('>III', block, 16)
        require(vid == 2048 and payload == 4096, 'unexpected NAND page geometry')
        sequence.add(seq)
        h = block[vid:vid + 64]
        require(h[:4] == b'UBI!', 'VID magic')
        require(struct.unpack_from('>I', h, 60)[0] == (~zlib.crc32(h[:60]) & 0xffffffff), 'VID CRC')
        volume, lnum = struct.unpack_from('>II', h, 8)
        if volume >= 0x7fffefff:
            tables.append(block[payload:payload + 128 * 172])
        else:
            pieces = volumes.setdefault(volume, {})
            require(lnum not in pieces, 'duplicate LEB')
            pieces[lnum] = block[payload:]
    require(len(sequence) == 1 and len(tables) == 2 and tables[0] == tables[1], 'UBI layout copies differ')
    names = {}
    for index in range(128):
        rec = tables[0][index * 172:(index + 1) * 172]
        require(len(rec) == 172, 'short volume table')
        require(struct.unpack_from('>I', rec, 168)[0] == (~zlib.crc32(rec[:168]) & 0xffffffff), 'volume table CRC')
        if struct.unpack_from('>I', rec)[0]:
            length = struct.unpack_from('>H', rec, 14)[0]
            names[index] = rec[16:16 + length].decode('ascii')
    require({'kernel', 'rootfs'} <= set(names.values()), 'missing UBI volume')
    require(set(names.values()) <= {'kernel', 'rootfs', 'rootfs_data'}, 'unexpected factory volume')
    for number, name in names.items():
        if name not in expected:
            continue
        pieces = volumes[number]
        require(sorted(pieces) == list(range(len(pieces))), 'noncontiguous logical UBI image')
        actual = b''.join(pieces[x] for x in sorted(pieces))
        wanted = expected[name].read_bytes()
        if name == 'rootfs':
            require(wanted[:4] == b'hsqs' and len(wanted) >= 96, 'not squashfs')
            used = struct.unpack_from('<Q', wanted, 40)[0]
            require(96 <= used <= len(wanted), 'squashfs size invalid')
            require(not wanted[used:].strip(b'\x00\xff'), 'unexpected squashfs tar padding')
            wanted = wanted[:used]
        require(actual[:len(wanted)] == wanted, 'factory/sysupgrade ' + name + ' mismatch')
        require(not actual[len(wanted):].strip(b'\xff'), 'unexpected payload after volume')
    return {'pebs': len(data) // 0x20000, 'volumes': names, 'CRC': 'PASS', 'payload_equality': 'PASS'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root', required=True, type=pathlib.Path)
    p.add_argument('--output', required=True, type=pathlib.Path)
    p.add_argument('--reference-image', type=pathlib.Path,
                   help='Known-good 24.10 image; required to authorize the attended transition, not CI static checks')
    args = p.parse_args()
    build, out = args.build_root.resolve(), args.output.resolve()
    require(not out.exists(), 'output must be a new directory')
    require(not subprocess.check_output(['git', '-C', str(build), 'status', '--porcelain']), 'build tree is dirty')
    identity = json.loads((build / 'rainwrt-build-identity.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(build), 'rev-parse', 'HEAD'], text=True).strip()
    require(identity['RAINWRT_SOURCE_REVISION'] == commit, 'source identity mismatch')
    target = build / 'bin/targets/qualcommax/ipq50xx'
    out.mkdir(parents=True, mode=0o700)
    names = [PREFIX + s for s in ('-squashfs-sysupgrade.bin', '-squashfs-factory.ubi', '-initramfs-uImage.itb', '.manifest')]
    names += ['config.buildinfo', 'feeds.buildinfo', 'version.buildinfo', 'profiles.json']
    for name in names:
        shutil.copyfile(target / name, out / name)
    shutil.copyfile(build / 'rainwrt-build-identity.json', out / 'source-identity.json')
    shutil.copyfile(ROOT / 'docs/HARDWARE_TEST_25_12.md', out / 'HARDWARE_TEST_25_12.md')
    host = build / 'staging_dir/host/bin'
    image = out / names[0]
    subprocess.run([str(host / 'fwtool'), '-i', str(out / 'image-metadata.json'), str(image)], check=True)
    metadata = json.loads((out / 'image-metadata.json').read_text())
    require(metadata['supported_devices'] == ['redmi,ax3000'], 'wrong supported_devices')
    require(metadata['version']['target'] == 'qualcommax/ipq50xx', 'wrong target')
    extracted = out / 'static-inspection'
    extracted.mkdir()
    with tarfile.open(image) as archive:
        members = archive.getmembers()
        for member in members:
            require(not member.issym() and not member.islnk() and '..' not in pathlib.PurePosixPath(member.name).parts, 'unsafe sysupgrade tar')
        parts = {}
        for name in ('kernel', 'root'):
            found = [m for m in members if m.isfile() and m.name.endswith('/' + name)]
            require(len(found) == 1, 'missing/duplicate sysupgrade member')
            parts[name] = extracted / name
            with archive.extractfile(found[0]) as src, parts[name].open('wb') as dst:
                shutil.copyfileobj(src, dst)
    ubi = inspect_ubi(out / names[1], {'kernel': parts['kernel'], 'rootfs': parts['root']})
    rootfs = extracted / 'rootfs'
    # Fakeroot handles the inert /dev/console inode without host root privileges.
    subprocess.run(['fakeroot', str(host / 'unsquashfs4'), '-d', str(rootfs), str(parts['root'])], check=True, stdout=subprocess.DEVNULL)
    parsed = dict(re.findall(r"^(RAINWRT_[A-Z_]+)='([^']+)'$", (rootfs / 'etc/rainwrt-release').read_text(), re.M))
    require(parsed == identity, 'runtime identity mismatch')
    modules = list((rootfs / 'lib/modules').iterdir())
    require(len(modules) == 1, 'ambiguous module kernel version')
    kernel = modules[0].name
    manifest = (out / names[3]).read_text()
    for package in ('kmod-wireguard', 'wireguard-tools', 'luci-proto-wireguard', 'wpad-openssl', 'luci',
                    'luci-ssl-openssl', 'luci-i18n-base-zh-cn', 'ath11k-firmware-ipq5018-qcn6122', 'ipq-wifi-redmi_ax3000'):
        require(re.search('^' + re.escape(package) + r' - ', manifest, re.M), 'missing package ' + package)
    require((rootfs / 'usr/bin/wg').is_file(), 'wg binary missing')
    require(list(modules[0].glob('wireguard.ko*')), 'wireguard module missing')
    require('/lib/upgrade/*.sh' in (rootfs / 'lib/upgrade/stage2').read_text(), 'stage2 lost helpers')
    for name in ('mi_layout.sh', 'mi_dualboot.sh', 'platform.sh'):
        require(sha(rootfs / 'lib/upgrade' / name) == sha(build / 'target/linux/qualcommax/ipq50xx/base-files/lib/upgrade' / name), 'installed helper mismatch')
    require('CONFIG_ATH11K_SMALLBUFFERS=y' in (build / '.config').read_text(), 'lost low-memory config')
    repo = rootfs / 'etc/apk/repositories.d/distfeeds.list'
    require(not any(l.strip() and not l.startswith('#') for l in repo.read_text().splitlines()), 'mismatching public feed enabled')
    for name in (names[2],):
        result = subprocess.run([str(host / 'mkimage'), '-l', str(out / name)], capture_output=True, check=True)
        (out / (name + '.fit.txt')).write_bytes(result.stdout)
    shutil.copytree(target / 'packages', out / 'packages/core')
    shutil.copytree(build / 'bin/packages/aarch64_cortex-a53', out / 'packages/feeds')
    # Only public verification keys belong in the package.
    shutil.copytree(rootfs / 'etc/apk/keys', out / 'packages/keys')
    licenses = list((build / 'build_dir/target-aarch64_cortex-a53_musl').glob('ath11k-legacy-firmware-*/ath11k-firmware/LICENSE.md'))
    require(len(licenses) == 1, 'vendor firmware notice missing')
    shutil.copyfile(licenses[0], out / 'QUALCOMM-FIRMWARE-LICENSE.txt')
    tool_names = ['scripts/attended-cr8808-hardware-test.sh', 'scripts/hardware_test.py', 'scripts/lib/cr8808-probe.sh',
                  'scripts/performance-audit.sh', 'target/linux/qualcommax/ipq50xx/base-files/lib/upgrade/mi_layout.sh']
    for name in tool_names:
        destination = out / 'runner' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    baseline_helpers = {}
    if args.reference_image:
        require(sha(args.reference_image) == 'bd552ead7a42f1355195c9dc72eb7bcf798886f4886fba86d5c29d3aa0e7e7d1', 'wrong reference image')
        with tarfile.open(args.reference_image) as archive:
            roots = [m for m in archive.getmembers() if m.isfile() and m.name.endswith('/root')]
            require(len(roots) == 1, 'reference rootfs missing')
            reference = extracted / 'reference-root.squashfs'
            with archive.extractfile(roots[0]) as src, reference.open('wb') as dst:
                shutil.copyfileobj(src, dst)
        helper_paths = ['/sbin/sysupgrade', '/lib/upgrade/stage2', '/lib/upgrade/do_stage2',
                        '/lib/upgrade/platform.sh', '/lib/upgrade/mi_layout.sh', '/lib/upgrade/mi_dualboot.sh',
                        '/lib/upgrade/nand.sh', '/lib/upgrade/common.sh']
        for name in helper_paths:
            content = subprocess.check_output([str(host / 'unsquashfs4'), '-cat', str(reference), name.lstrip('/')])
            require(bool(content), 'reference helper missing')
            baseline_helpers[name] = hashlib.sha256(content).hexdigest()
        reference.unlink()  # Only this invocation's extracted temporary copy.
    files = {p.name: sha(p) for p in out.iterdir() if p.is_file()}
    result = {'source_revision': commit, 'identity': identity, 'kernel': kernel, 'image': image.name,
              'files': files, 'tools': {n: sha(ROOT / n) for n in tool_names}, 'UBI': ubi, 'baseline_helpers': baseline_helpers,
              'status': 'STATIC_STRUCTURE_PASS_HARDWARE_UNTESTED'}
    (out / 'candidate.json').write_text(json.dumps(result, indent=2) + '\n')
    checksums = []
    for path in sorted(out.rglob('*')):
        if path.is_file() and not path.is_symlink():
            checksums.append(sha(path) + '  ' + path.relative_to(out).as_posix())
    (out / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n')
    print(json.dumps({'candidate': str(out), 'manifest_sha256': sha(out / 'candidate.json'), 'kernel': kernel, 'UBI': ubi}))


if __name__ == '__main__':
    main()
