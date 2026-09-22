#!/usr/bin/env python3
"""Offline package/ELF and differential SquashFS measurements, never an image build."""
import argparse
import json
import pathlib
import re
import struct
import subprocess
import tempfile


def run(args):
    return subprocess.check_output([str(x) for x in args], stderr=subprocess.DEVNULL)


def resolve(root, name):
    parts = list(pathlib.PurePosixPath(name).parts)
    result = root
    for _ in range(100):
        if not parts:
            return result
        part = parts.pop(0)
        if part == '/':
            result = root
        elif part == '..':
            result = result.parent if result != root else root
        else:
            result /= part
            if result.is_symlink():
                target = result.readlink()
                result = root if target.is_absolute() else result.parent
                parts = list(target.parts) + parts
    raise RuntimeError('symlink loop')


def closure(root, bins):
    paths, todo = set(), []
    for binary in bins:
        for directory in ('usr/sbin', 'usr/bin', 'sbin', 'bin'):
            p = resolve(root, '/' + directory + '/' + binary)
            if p.is_file():
                todo.append(p)
                break
    while todo:
        p = todo.pop()
        if p in paths:
            continue
        paths.add(p)
        data = subprocess.run(['readelf', '-d', '-l', str(p)], capture_output=True).stdout.decode()
        libs = re.findall(r'Shared library: \[([^\]]+)\]', data)
        libs += re.findall(r'Requesting program interpreter: ([^\]]+)', data)
        for lib in libs:
            candidates = [resolve(root, lib)] if lib.startswith('/') else [resolve(root, d + lib) for d in ('/lib/', '/usr/lib/')]
            target = next((q for q in candidates if q.is_file()), None)
            if target is None:
                raise RuntimeError('missing ELF dependency ' + lib)
            todo.append(target)
    return paths


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=pathlib.Path, required=True)
    p.add_argument('--build-root', type=pathlib.Path, required=True)
    p.add_argument('--legacy-root', type=pathlib.Path, required=True)
    args = p.parse_args()
    root = args.candidate / 'static-inspection/rootfs'
    apk = args.build_root / 'staging_dir/host/bin/apk'
    packages = json.loads(run([apk, '--root', root, '--no-network', 'query', '--installed', '--format', 'json',
                              '--fields', 'name,installed-size,depends', '--all-matches', '*']))
    db = {x['name']: x for x in packages}
    selected = ['luci', 'luci-i18n-base-zh-cn', 'luci-ssl-openssl', 'kmod-wireguard', 'wireguard-tools',
                'luci-proto-wireguard', 'wpad-openssl', 'curl', 'ca-bundle', 'tcpdump', 'iperf3', 'jq', 'htop', 'nano']
    def files(names):
        result = set()
        for name in names:
            listing = root / ('lib/apk/packages/' + name + '.list')
            if listing.exists():
                result.update(n.lstrip('/') for n in listing.read_text().splitlines() if n.startswith('/')
                              and not (root / n.lstrip('/')).is_dir())
        return result
    def depends(name):
        result, todo = set(), [name]
        while todo:
            q = todo.pop()
            if q in result or q not in db:
                continue
            result.add(q)
            todo += [re.split('[<>=~]', x)[0] for x in db[q].get('depends', []) if not x.startswith('!')]
        return sorted(result)
    optional = {'tcpdump', 'iperf3', 'htop', 'nano'}
    removable = set(optional)
    possible = set().union(*(set(depends(n)) for n in optional))
    while True:
        extra = {n for n in possible - removable if not any(
            n in [re.split('[<>=~]', d)[0] for d in x.get('depends', [])] for key, x in db.items() if key not in removable)}
        if not extra:
            break
        removable |= extra
    squash = args.build_root / 'staging_dir/host/bin/mksquashfs4'
    with tempfile.TemporaryDirectory(prefix='rainwrt-footprint-') as temp:
        temp = pathlib.Path(temp)
        def compressed(label, exclude):
            exclusions = temp / (label + '.exclude')
            exclusions.write_text('\n'.join(sorted(exclude)) + '\n')
            image = temp / (label + '.squashfs')
            command = [squash, root, image, '-noappend', '-no-xattrs', '-all-root', '-comp', 'xz', '-b', '256k',
                       '-Xpreset', '9', '-Xe', '-Xlc', '0', '-Xlp', '2', '-Xpb', '2', '-processors', '2', '-no-progress']
            if exclude:
                command += ['-ef', exclusions]
            run(command)
            with image.open('rb') as stream:
                stream.seek(40)
                return struct.unpack('<Q', stream.read(8))[0]
        baseline = compressed('baseline', set())
        rows = []
        for name in selected:
            row = dict(db[name], dependency_closure=depends(name))
            row['payload_bytes'] = sum((root / n).lstat().st_size for n in files([name]))
            row['differential_squashfs_bytes'] = baseline - compressed(name, files([name]))
            rows.append(row)
        group_saving = baseline - compressed('optional-closure', files(removable))
    bins = 'busybox ash sh mount umount pivot_root mount_root reboot sync kill sleep md5sum hexdump cat zcat dd tar gzip ls basename find cp mv rm mkdir rmdir mknod touch chmod printf wc grep awk sed cut sort tail mtd partx losetup mkfs.ext4 nandwrite flash_erase ubiupdatevol ubiattach ubiblock ubiformat ubidetach ubirsvol ubirmvol ubimkvol snapshot snapshot_tool date logger fw_printenv fw_setenv fwtool dumpimage head seq sha256sum upgraded ubus'.split()
    closures = {}
    for label, tree in [('known_good_24.10', args.legacy_root), ('candidate_25.12.2', root)]:
        ps = closure(tree, bins)
        ps |= {q for base in ('lib/upgrade', 'lib/functions') for q in (tree / base).rglob('*') if q.is_file() and not q.is_symlink()}
        ps |= set((tree / 'lib').glob('*.sh'))
        ps |= {tree / q for q in ('usr/share/libubox/jshn.sh', 'etc/fw_env.config') if (tree / q).is_file()}
        handoff = closure(tree, ['upgraded'])
        closures[label] = {'file_count': len(ps), 'stage2_page_kib': sum((q.stat().st_size + 4095)//4096*4 for q in ps),
                           'handoff_page_kib': sum((q.stat().st_size + 4095)//4096*4 for q in handoff)}
    with tempfile.TemporaryDirectory(prefix='rainwrt-optional-feed-') as directory:
        command = [apk, '--keys-dir', args.candidate / 'packages/keys', '--arch', 'aarch64_cortex-a53', '--no-network', '--no-cache']
        for index in sorted((args.candidate / 'packages').rglob('packages.adb')):
            command += ['-X', index]
        run(command + ['fetch', '-R', '-o', directory] + sorted(optional | {'jq'}))
        fetched = len(list(pathlib.Path(directory).glob('*.apk')))
    print(json.dumps({'packages': rows, 'repacked_baseline_bytes': baseline, 'optional_removable_closure': sorted(removable),
                      'optional_closure_squashfs_saving_bytes': group_saving, 'closures': closures,
                      'signed_offline_optional_feed_packages_fetched': fetched,
                      'note': 'Differential repack only, not a bootable candidate; APK database retained, marginal sizes non-additive.'}, indent=2))


if __name__ == '__main__':
    main()
