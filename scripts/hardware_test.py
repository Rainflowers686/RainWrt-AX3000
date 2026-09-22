#!/usr/bin/env python3
"""Attended CR8808 transition. Transport is injectable; no retry of any write."""
import argparse
import datetime
import fcntl
import gzip
import hashlib
import io
import ipaddress
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
MIBIB = 'b0c9f1a0239bd150e121063278d123b30e7697a6959ea4543cce8e83aa47ca54'
APPSBL = 'a92f08878499bb697e67cfb5f597bb5757e48b4846f4f250fbc612ea166ad4f3'
RECOVERY = '7b48d723d93612c6fb8857ec4f05ac7faf62242f6848e5686f53fc8ff6752e69'
DETECTOR = 'target/linux/qualcommax/ipq50xx/base-files/lib/upgrade/mi_layout.sh'
MEMORY_TOOL = 'scripts/lib/upgrade-memory.sh'
BASELINE_HELPERS = {'/sbin/sysupgrade', '/lib/upgrade/stage2', '/lib/upgrade/do_stage2',
                    '/lib/upgrade/platform.sh', '/lib/upgrade/mi_layout.sh', '/lib/upgrade/mi_dualboot.sh',
                    '/lib/upgrade/nand.sh', '/lib/upgrade/common.sh'}
SERVICE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z')
HANDOFF = re.compile(r'Commencing upgrade|Closing all shell sessions|RAINWRT_SYSUPGRADE_INVOKED')
ENABLED_SERVICES = 'for p in /etc/rc.d/S*; do [ -L "$p" ] && [ -x "$p" ] || continue; readlink "$p"; done\n'


class Stop(Exception):
    pass


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def private_write(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as f:
        f.write(data if isinstance(data, bytes) else data.encode())
        f.flush()
        os.fsync(f.fileno())


def layout_checks(p):
    return {
        'board': p['board'] == 'redmi,ax3000',
        'mtd18': bool(re.search(r'^mtd18: 07480000 00020000 "rootfs"$', p['mtd'], re.M)),
        'mtd_character': p['char'] is True,
        'rootfs_1_absent': '"rootfs_1"' not in p['mtd'],
        'rootfs_offset': p['offset'] == 0xA80000,
        'cmdline': p['cmdline'] is True,
        'mibib': p['mibib'] == MIBIB and bool(re.search(r'^mtd1: .* "0:MIBIB"$', p['mtd'], re.M)),
        'appsbl': p['appsbl'] == APPSBL and bool(re.search(r'^mtd12: .* "0:APPSBL"$', p['mtd'], re.M)),
        'bootcmd': p['bootcmd'] == 'bootmiwifi',
    }


def detector_check(path):
    # OpenWrt libraries intentionally use unset optional variables. Isolate
    # their shell semantics; keep nounset on the outer verification script.
    return '[ "$(set +u; . ' + shlex.quote(path) + '; mi_layout_detect)" = rainwrt-single-slot ]\n'


def phase_requirements(profile, sample, image_kib=0, archive_bytes=0, staged=False):
    """See SYSUPGRADE_MEMORY_MODEL.md; no kernel/cache reclamation credit.

    The original 8 MiB operational margin remains in every physical gate.
    Anonymous-memory credit is capped to deferred RAM_ROOT files only, never
    spent on that margin or the running-system upload/validation phase.
    """
    h, r = profile['handoff'][1], profile['stage2'][1]
    if any(type(n) is not int for n in (h, r)) or not 128 <= h <= r <= 16384:
        raise Stop('PRECHECK_FAILED: invalid measured upgrade closure')
    keys = ('mem_kib', 'tmp_kib', 'anon_kib', 'observer_anon_kib', 'locked_kib', 'swap_kib')
    if any(type(sample.get(k)) is not int or sample[k] < 0 for k in keys):
        raise Stop('PRECHECK_FAILED: invalid resource sample')
    config_kib = (archive_bytes + 4095) // 4096 * 4
    pending_config = config_kib if staged else 2 * config_kib
    credit = 0 if sample['locked_kib'] or sample['swap_kib'] else min(r, max(0, sample['anon_kib'] - sample['observer_anon_kib']))
    running = h + 8192 + pending_config
    after_cleanup = r + 8192 + pending_config
    return {'physical_required_kib': image_kib + max(running, after_cleanup - credit),
            'tmp_required_kib': image_kib + 2 * r + pending_config,
            'running_phase_kib': running, 'ramfs_phase_kib': after_cleanup,
            'deferred_file_credit_kib': credit, 'pending_config_kib': pending_config,
            'handoff_file_kib': h, 'ramfs_file_kib': r, 'transient_margin_kib': 8192}


def wait_resources(sample, image_kib, profile, emit, phase, archive_bytes=0, staged=False,
                   clock=time.monotonic, sleep=time.sleep):
    """Phase-aware budget; two fresh samples five seconds apart within 120 s.

    Only the light resource probe is repeated, not the stage2 library scan.
    The monotonic deadline includes SSH sampling time. No reclaim or writes.
    """
    start = clock()
    end = start + 120
    consecutive = 0
    while clock() < end:
        p = sample(timeout=min(10, end - clock()))
        budget = phase_requirements(profile, p, image_kib, archive_bytes, staged)
        consecutive = consecutive + 1 if p['mem_kib'] >= budget['physical_required_kib'] and p['tmp_kib'] >= budget['tmp_required_kib'] else 0
        emit('RESOURCE_SAMPLE', {'phase': phase, 'elapsed_seconds': round(clock() - start, 3),
                                'mem_kib': p['mem_kib'], 'tmp_kib': p['tmp_kib'],
                                'image_upload_kib': image_kib, **budget, 'consecutive': consecutive})
        if clock() >= end:
            break
        if consecutive >= 2:
            emit('RESOURCE_PASS', {'phase': phase, **budget})
            return p
        sleep(min(5, end - clock()))
    raise Stop('PRECHECK_FAILED: resource stability timeout (120 seconds; phase-aware budgets)')


def required_checks(p, expected, baseline):
    checks = layout_checks(p)
    checks.update({
        'exact_build_identity': p['identity'] == expected['identity'],
        'kernel': p['kernel'] == expected['kernel'],
        'release': p['release']['release'] == expected['identity']['RAINWRT_UPSTREAM_VERSION'],
        'target': p['release']['target'] == 'qualcommax/ipq50xx',
        'ubi': p['ubi_mtd'] == 18 and set(p['ubi'].split()) == {'kernel', 'rootfs', 'rootfs_data'},
        'root_mount': bool(re.search(r'^/ overlay ', p['mounts'], re.M)),
        'overlay_mount': bool(re.search(r'^/overlay ubifs ', p['mounts'], re.M)),
        'no_fatal_errors': p['fatal'] is False,
        'IPQ5018': 'c000000.wifi' in p['phy'] and '0x10' in p['bdf'].split(),
        'QCN6122': len(p['phy'].split()) == 2 and '0x60' in p['bdf'].split() and p['rproc'].split().count('running') >= 3,
        'wireless': p['bands'] == '1 1' and len(p['wifi']) == 2 and all(r['disabled'] or (r['up'] and not r['pending']) for r in p['wifi']),
        'ethernet': set('lan1 lan2 lan3 wan br-lan'.split()) <= set(p['ports'].split()) and p['carrier'],
        'WireGuard': p['wg'] and p['wg_abi'] == expected['kernel'],
        'APK_packages': p['apk'] is True,
        'IPv4_route': not baseline['ipv4'] or p['ipv4'],
        'IPv6_route': not baseline['ipv6'] or p['ipv6'],
        'resolver': not baseline['resolver'] or p['resolver'],
    })
    return checks


def classify_return(p, expected, baseline):
    if p['boot_id'] == baseline['boot_id']:
        return 'WAITING_FOR_RETURN'
    if p['identity'] != expected['identity']:
        return 'RETURNED_OLD_SYSTEM' if p['release'] == baseline['release'] else 'RETURNED_WRONG_BUILD'
    return 'SUCCESS' if all(required_checks(p, expected, baseline).values()) else 'POSTCHECK_FAILED'


def handoff_state(code, output):
    if HANDOFF.search(output):
        return 'EXPECTED_HANDOFF' if 'Commencing upgrade' in output or 'Closing all shell sessions' in output else 'INDETERMINATE_HANDOFF'
    return 'INDETERMINATE_HANDOFF' if code in (0, 246, 255, 124) else 'PRE_HANDOFF_FAILURE'


def migrate_archive(source, destination, enabled):
    """Opaque bytes only: never extract, source, evaluate or print user data."""
    removed, preserved, seen, disabled = 0, {}, set(), set()
    blocked = ('etc/opkg', 'usr/lib/opkg', 'etc/apk', 'lib/apk', 'lib/upgrade', 'etc/rc.d')
    exact = {'etc/rainwrt-release', 'etc/init.d/uboot_env', 'etc/uci-defaults/10_disable_services',
             'etc/uci-defaults/91-rainwrt-preserved-services'}
    with tarfile.open(source, 'r:gz') as src, tarfile.open(destination, 'w:gz', format=tarfile.PAX_FORMAT) as dst:
        members = src.getmembers()
        if sum(x.size for x in members) > 16 * 1024 * 1024:
            raise Stop('PRECHECK_FAILED: configuration exceeds audited 16 MiB budget')
        for member in members:
            name = member.name.removeprefix('./').lstrip('/')
            if '..' in pathlib.PurePosixPath(name).parts or name in seen or '\n' in name or '\x00' in name:
                raise Stop('PRECHECK_FAILED: unsafe archive member')
            seen.add(name)
            if name == 'etc/uci-defaults/10_disable_services':
                if not member.isfile():
                    raise Stop('PRECHECK_FAILED: invalid upstream service-state member')
                for line in src.extractfile(member).read().decode().splitlines():
                    if line.strip() in ('', 'exit 0'):
                        continue
                    match = re.fullmatch(r'/etc/init.d/([A-Za-z0-9][A-Za-z0-9_.-]{0,63}) disable', line)
                    if not match:
                        raise Stop('PRECHECK_FAILED: unrecognized upstream disable-state format')
                    disabled.add(match[1])
            if member.islnk() or member.isdev() or member.isfifo():
                raise Stop('PRECHECK_FAILED: unsupported archive member type')
            if member.issym():
                target = pathlib.PurePosixPath(member.linkname)
                if target.is_absolute() or '..' in target.parts:
                    raise Stop('PRECHECK_FAILED: unsafe archive link')
            if name in exact or any(name == x or name.startswith(x + '/') for x in blocked):
                removed += 1
                continue
            member.name = name
            stream = src.extractfile(member) if member.isfile() else None
            if name.startswith('etc/init.d/'):
                service = name[len('etc/init.d/'):]
                if not SERVICE.fullmatch(service) or not member.isfile():
                    raise Stop('PRECHECK_FAILED: unsafe preserved service')
                data = stream.read()
                if service in enabled:
                    preserved[service] = hashlib.sha256(data).hexdigest()
                stream = io.BytesIO(data)
            dst.addfile(member, stream)
        # Generated only from original enabled links, safe names and exact
        # preserved script bytes. Invoke normal rc.common enable semantics.
        if enabled & disabled:
            raise Stop('PRECHECK_FAILED: inconsistent original service state')
        if preserved or disabled:
            lines = ['#!/bin/sh', 'set -eu']
            for name in sorted(disabled):
                path = '/etc/init.d/' + name
                lines += [f'if [ -f {path} ] && [ ! -L {path} ]; then',
                          f'  /bin/sh /etc/rc.common {path} disable', 'fi']
            for name, digest in sorted(preserved.items()):
                path = '/etc/init.d/' + name
                lines += [f'[ -f {path} ] && [ ! -L {path} ]',
                          f'[ "$(sha256sum {path} | cut -d\' \' -f1)" = {digest} ]',
                          f'/bin/sh /etc/rc.common {path} enable']
            lines += ['exit 0', '']
            data = '\n'.join(lines).encode()
            info = tarfile.TarInfo('etc/uci-defaults/91-rainwrt-preserved-services')
            info.size, info.mode, info.uid, info.gid = len(data), 0o700, 0, 0
            dst.addfile(info, io.BytesIO(data))
    os.chmod(destination, 0o600)
    with tarfile.open(destination) as result:
        names = set(result.getnames())
        if any(any(x == b or x.startswith(b + '/') for b in blocked) for x in names):
            raise Stop('PRECHECK_FAILED: stale feed or upgrade helper survived migration')
    return {'removed_members': removed, 'enabled_custom_services': preserved, 'disabled_services': sorted(disabled)}


def audit_archive(original, migrated):
    """Report only booleans/counts; validate gzip CRC and preserved core bytes."""
    with gzip.open(migrated, 'rb') as stream:
        while stream.read(65536):
            pass  # Read through the trailer, not just the first tar end marker.
    with tarfile.open(original) as old, tarfile.open(migrated) as new:
        old_members = {m.name.removeprefix('./').lstrip('/'): m for m in old.getmembers()}
        members = {m.name: m for m in new.getmembers()}
        core = {'etc/config/' + n for n in ('network', 'wireless', 'dhcp', 'firewall', 'system')}
        keys = {n for n in old_members if n.startswith('etc/dropbear/') and n.endswith('_host_key')}
        def same_bytes(names):
            return all(n in members and n in old_members and members[n].isfile() and old_members[n].isfile()
                       and new.extractfile(members[n]).read() == old.extractfile(old_members[n]).read() for n in names)
        checks = {'core_config_preserved': same_bytes(core),
                  'SSH_host_keys_preserved': bool(keys) and same_bytes(keys),
                  'archive_integrity': True}
        for label, prefixes in {'old_opkg_removed': ('etc/opkg', 'usr/lib/opkg'),
                                'old_apk_removed': ('etc/apk', 'lib/apk'),
                                'old_upgrade_removed': ('lib/upgrade',),
                                'old_rc_d_removed': ('etc/rc.d',)}.items():
            checks[label] = not any(n == p or n.startswith(p + '/') for n in members for p in prefixes)
        if not all(checks.values()):
            raise Stop('PRECHECK_FAILED: config preservation/integrity audit')
        return dict(checks, core_config_count=len(core), SSH_host_key_count=len(keys), member_count=len(members))


class Transport:
    def __init__(self, host, state):
        ipaddress.IPv4Address(host)
        self.host = host
        known = state / 'known_hosts'
        if not known.exists():
            existing = pathlib.Path.home() / '.ssh/known_hosts'
            data = b''
            if existing.exists():
                result = subprocess.run(['ssh-keygen', '-F', host, '-f', str(existing)], capture_output=True, check=False)
                data = result.stdout
            private_write(known, data)
        self.options = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', '-o', 'ConnectionAttempts=1',
                        '-o', 'StrictHostKeyChecking=accept-new', '-o', 'UserKnownHostsFile=' + str(known),
                        '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=3']

    def run(self, script, timeout=90):
        try:
            return subprocess.run(['ssh', *self.options, 'root@' + self.host, 'sh -s'], input=script.encode(),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as e:
            return subprocess.CompletedProcess([], 124, e.stdout or b'', e.stderr or b'')

    def checked(self, script, timeout=90):
        r = self.run(script, timeout)
        if r.returncode:
            if b'HOST IDENTIFICATION HAS CHANGED' in r.stderr or b'Host key verification failed' in r.stderr:
                raise Stop('SSH_HOST_KEY_CHANGED')
            raise Stop('PRECHECK_FAILED: remote command failed (private output withheld)')
        return r.stdout

    def copy(self, local, remote):
        r = subprocess.run(['scp', '-O', *self.options, str(local), 'root@' + self.host + ':' + remote],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
        if r.returncode:
            raise Stop('PRECHECK_FAILED: transfer failed')

    def probe(self):
        return json.loads(self.checked((ROOT / 'scripts/lib/cr8808-probe.sh').read_text()))

    def resources(self, timeout):
        return json.loads(self.checked((ROOT / MEMORY_TOOL).read_text() + '\nmemory_sample\n', timeout=timeout))

    def memory_profile(self):
        return json.loads(self.checked((ROOT / MEMORY_TOOL).read_text() + '\nmemory_profile\n'))


class Controller:
    def __init__(self, transport, expected, baseline, emit, clock=time.monotonic, sleep=time.sleep):
        self.transport, self.expected, self.baseline, self.emit = transport, expected, baseline, emit
        self.clock, self.sleep = clock, sleep
        self.writes = 0
        self.reboots = 0

    def wait_return(self, previous, reboot=False):
        end = self.clock() + 600
        self.emit('WAITING_FOR_RETURN')
        self.sleep(35)
        while self.clock() < end:
            try:
                p = self.transport.probe()
            except (Stop, ValueError, KeyError) as e:
                if str(e) == 'SSH_HOST_KEY_CHANGED':
                    raise
                self.sleep(5)
                continue
            if p['boot_id'] == previous['boot_id']:
                self.sleep(5)
                continue
            # Give radios/services time to initialize, while preserving deadline.
            state = classify_return(p, self.expected, previous)
            if state in ('RETURNED_OLD_SYSTEM', 'RETURNED_WRONG_BUILD'):
                raise Stop('REBOOT_VALIDATION_FAILED' if reboot else state)
            if state == 'SUCCESS':
                return p
            if p['uptime'] < 120:
                self.sleep(5)
                continue
            self.emit('required_checks', required_checks(p, self.expected, self.baseline))
            raise Stop('REBOOT_VALIDATION_FAILED' if reboot else 'POSTCHECK_FAILED')
        raise Stop('REBOOT_VALIDATION_FAILED' if reboot else 'FAILED_TO_RETURN')

    def execute(self, command):
        if self.writes:
            raise Stop('REFUSING_SECOND_SYSUPGRADE')
        self.writes += 1
        result = self.transport.run(command, timeout=180)
        state = handoff_state(result.returncode, (result.stdout + result.stderr).decode(errors='replace'))
        self.emit(state)
        if state == 'PRE_HANDOFF_FAILURE':
            raise Stop(state)
        return self.wait_return(self.baseline)

    def reboot(self, previous):
        if self.reboots or not all(required_checks(previous, self.expected, self.baseline).values()):
            raise Stop('REFUSING_UNSAFE_OR_SECOND_REBOOT')
        self.reboots += 1
        self.emit('NORMAL_REBOOT_VALIDATION')
        self.transport.run('sync\nreboot\n', timeout=30)
        return self.wait_return(previous, reboot=True)


def network_check(transport, endpoints, ipv6=False):
    family = '-6' if ipv6 else '-4'
    for endpoint in endpoints:
        if not re.fullmatch(r'https://[a-zA-Z0-9.-]+/[a-zA-Z0-9/_.-]*', endpoint):
            raise Stop('PRECHECK_FAILED: invalid public endpoint')
        domain = endpoint.split('/')[2]
        script = f'nslookup {shlex.quote(domain)} >/dev/null 2>&1 && curl {family} -fLsS --max-time 12 --connect-timeout 5 --output /dev/null {shlex.quote(endpoint)}\n'
        if transport.run(script, timeout=20).returncode == 0:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--validate-reboot', action='store_true')
    parser.add_argument('--candidate-dir', type=pathlib.Path)
    parser.add_argument('--recovery-dir', type=pathlib.Path)
    parser.add_argument('--host', default='192.168.1.1')
    parser.add_argument('--endpoint', action='append')
    args = parser.parse_args()
    os.umask(0o077)
    state = pathlib.Path(os.environ.get('XDG_STATE_HOME', pathlib.Path.home() / '.local/state')) / 'rainwrt'
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(state, 0o700)
    lock = (state / 'hardware-test.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    settings_path = state / 'hardware-test.json'
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    run = state / ('test-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
    run.mkdir(mode=0o700)
    def emit(event, detail=None):
        record = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'event': event}
        if detail is not None:
            record['detail'] = detail
        with (run / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(record) + '\n')
            stream.flush()
        print(event, json.dumps(detail) if detail is not None else '', flush=True)
    attempted = False
    try:
        for tool in ('ssh', 'scp', 'ssh-keygen', 'shellcheck'):
            if not shutil.which(tool):
                raise Stop('PRECHECK_FAILED: missing local tool ' + tool)
        candidate = args.candidate_dir or pathlib.Path(settings.get('candidate_dir', ROOT / 'hardware-test-candidate'))
        manifest_path = candidate / 'candidate.json'
        expected = json.loads(manifest_path.read_text())
        anchor = settings.get('manifest_sha256')
        if not anchor or sha(manifest_path) != anchor:
            raise Stop('PRECHECK_FAILED: candidate manifest has no matching local review anchor')
        for name, digest in expected['files'].items():
            if '/' in name or name in ('.', '..') or sha(candidate / name) != digest:
                raise Stop('PRECHECK_FAILED: candidate file SHA mismatch')
        for name, digest in expected['tools'].items():
            if '..' in pathlib.PurePosixPath(name).parts or not (name.startswith('scripts/') or name == DETECTOR) or sha(ROOT / name) != digest:
                raise Stop('PRECHECK_FAILED: runner/helper version mismatch')
        if not {DETECTOR, MEMORY_TOOL} <= expected['tools'].keys():
            raise Stop('PRECHECK_FAILED: unbound layout or memory tool')
        helpers = expected.get('baseline_helpers', {})
        if set(helpers) != BASELINE_HELPERS or not all(re.fullmatch('[0-9a-f]{64}', h) for h in helpers.values()):
            raise Stop('PRECHECK_FAILED: current-system stage2 helper hashes are not bound')
        reference_verify = 'set -eu\n' + ''.join(
            f'[ "$(sha256sum {path} | cut -d\' \' -f1)" = {digest} ]\n' for path, digest in sorted(helpers.items()))
        subprocess.run(['shellcheck', str(ROOT / 'scripts/attended-cr8808-hardware-test.sh'),
                        str(ROOT / 'scripts/lib/cr8808-probe.sh'), str(ROOT / MEMORY_TOOL), str(ROOT / 'scripts/performance-audit.sh')], check=True)
        image = candidate / expected['image']
        if shutil.disk_usage(state).free < image.stat().st_size * 4 + 64 * 1024 * 1024:
            raise Stop('PRECHECK_FAILED: local state storage too small')
        recovery_dir = args.recovery_dir or pathlib.Path(settings.get('recovery_dir', candidate))
        recovery = recovery_dir / 'rainwrt-redmi_ax3000-baseline-wg-web-recovery-factory.ubi'
        if sha(recovery) != RECOVERY:
            raise Stop('PRECHECK_FAILED: known-good recovery SHA mismatch')
        if not (candidate / 'HARDWARE_TEST_25_12.md').is_file():
            raise Stop('PRECHECK_FAILED: recovery instructions absent')
        metadata = json.loads((candidate / 'image-metadata.json').read_text())
        if metadata['supported_devices'] != ['redmi,ax3000'] or metadata['version']['target'] != 'qualcommax/ipq50xx':
            raise Stop('PRECHECK_FAILED: candidate metadata')
        if expected['identity']['RAINWRT_SOURCE_REVISION'] != expected['source_revision']:
            raise Stop('PRECHECK_FAILED: candidate source identity')
        source_commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', expected['source_revision'] + '^{commit}'], text=True).strip()
        if source_commit != expected['source_revision']:
            raise Stop('PRECHECK_FAILED: source commit is unavailable')
        emit('LOCAL_PREFLIGHT_PASS')
        transport = Transport(args.host, state)
        baseline = transport.probe()
        private_write(run / 'baseline.json', json.dumps(baseline, indent=2))
        checks = layout_checks(baseline)
        checks['known_good_source'] = baseline['kernel'] == '6.6.137' and baseline['release']['revision'] == 'r0-2b3c0919'
        emit('fingerprint', checks)
        if not all(checks.values()):
            raise Stop('PRECHECK_FAILED: fingerprint')
        transport.checked(reference_verify)
        emit('EXISTING_HELPER_HASH_PASS', {'count': len(helpers)})
        profile = transport.memory_profile()
        emit('MEMORY_PROFILE', profile)
        # Exact stable remote path allows reuse after a previous dry run, never
        # deletes another task's staging and avoids duplicate images in tmpfs.
        remote = '/tmp/rainwrt-hwtest-' + expected['files'][expected['image']][:16]
        remote_image = remote + '/candidate.bin'
        current = transport.run('sha256sum ' + remote_image + ' 2>/dev/null\n')
        reused = current.returncode == 0 and current.stdout.decode().split()[0] == expected['files'][expected['image']]
        image_kib = 0 if reused else (image.stat().st_size + 4095) // 4096 * 4
        wait_resources(transport.resources, image_kib, profile, emit, 'PRE_UPLOAD_CAPACITY_PHYSICAL_GATE')
        transport.checked('set -eu\numask 077\n[ ! -L ' + remote + ' ]\nmkdir -p ' + remote + '\nchmod 700 ' + remote +
                          '\nfor f in candidate.bin config.tgz mi_layout.sh metadata.json; do [ ! -L ' + remote + '/$f ]; done\n')
        listing = transport.checked('sysupgrade -l\n')
        private_write(run / 'sysupgrade-list.txt', listing)
        emit('SYSUPGRADE_LIST_COLLECTED', {'count': len(listing.splitlines())})
        # procd rcS execlp() cannot run non-executable targets. A stale S link
        # alone must not turn an upstream-disabled service into enabled state.
        services = transport.checked(ENABLED_SERVICES)
        enabled = set()
        for line in services.decode().splitlines():
            name = line.rsplit('/', 1)[-1]
            if not SERVICE.fullmatch(name):
                raise Stop('PRECHECK_FAILED: unsafe original service name')
            enabled.add(name)
        # Standard archive streams directly to the host; no router gzip extraction.
        original = transport.checked('sysupgrade -b -\n', timeout=90)
        private_write(run / 'config-original.tgz', original)
        migrated = run / 'config-migrated.tgz'
        migration = migrate_archive(run / 'config-original.tgz', migrated, enabled)
        archive_audit = audit_archive(run / 'config-original.tgz', migrated)
        emit('CONFIG_MIGRATION_PASS', {'removed_members': migration['removed_members'], 'preserved_enabled_custom_services': len(migration['enabled_custom_services']),
                                     'archive_size': migrated.stat().st_size, 'archive_sha256': sha(migrated),
                                     'audit': archive_audit})
        # Now that the exact configuration size is known, also budget its
        # copies before any payload upload, without weakening the first gate.
        wait_resources(transport.resources, image_kib, profile, emit, 'PRE_PAYLOAD_UPLOAD_GATE', migrated.stat().st_size)
        if not reused:
            transport.copy(image, remote_image)
        transport.copy(migrated, remote + '/config.tgz')
        detector_path = ROOT / DETECTOR
        transport.copy(detector_path, remote + '/mi_layout.sh')
        detector_hash = sha(detector_path)
        verify = reference_verify + f'''set -eu
[ "$(sha256sum {remote_image} | cut -d' ' -f1)" = {expected['files'][expected['image']]} ]
[ "$(sha256sum {remote}/config.tgz | cut -d' ' -f1)" = {sha(migrated)} ]
[ "$(sha256sum {remote}/mi_layout.sh | cut -d' ' -f1)" = {detector_hash} ]
{detector_check(remote + '/mi_layout.sh')}
sysupgrade -T {remote_image}
fwtool -i {remote}/metadata.json {remote_image}
[ "$(jsonfilter -i {remote}/metadata.json -e '@.supported_devices[0]')" = redmi,ax3000 ]
[ "$(jsonfilter -i {remote}/metadata.json -e '@.version.target')" = qualcommax/ipq50xx ]
grep -Fq '/lib/upgrade/*.sh' /lib/upgrade/stage2
for h in mi_layout.sh mi_dualboot.sh platform.sh nand.sh common.sh do_stage2; do [ -s /lib/upgrade/$h ]; done
'''
        transport.checked(verify)
        emit('REMOTE_IMAGE_VALIDATION_PASS', {'candidate_sha256': expected['files'][expected['image']],
                                            'detector': 'rainwrt-single-slot', 'sysupgrade_T': True,
                                            'metadata_board': 'redmi,ax3000', 'metadata_target': 'qualcommax/ipq50xx',
                                            'stage2_helpers': True})
        post_upload = transport.probe()
        wait_resources(transport.resources, 0, profile, emit, 'POST_UPLOAD_VALIDATION_GATE', migrated.stat().st_size, staged=True)
        if baseline['boot_id'] != post_upload['boot_id'] or baseline['mtd'] != post_upload['mtd']:
            raise Stop('PRECHECK_FAILED: device changed during preflight')
        endpoints = args.endpoint or ['https://www.cloudflare.com/cdn-cgi/trace', 'https://www.wikipedia.org/']
        baseline_net = {family: network_check(transport, endpoints, family == 'ipv6') for family in ('ipv4', 'ipv6') if baseline[family]}
        private_write(run / 'network-baseline.json', json.dumps(baseline_net))
        emit('NETWORK_BASELINE_COLLECTED', baseline_net)
        wait_resources(transport.resources, 0, profile, emit, 'PRE_HANDOFF_GATE', migrated.stat().st_size, staged=True)
        final_memory_check = ((ROOT / MEMORY_TOOL).read_text() + '\nmemory_pre_handoff ' +
                              str(profile['stage2'][1]) + ' ' + str(profile['handoff'][1]) + ' ' +
                              str((migrated.stat().st_size + 4095) // 4096 * 4) + '\n')
        transport.checked(final_memory_check)
        emit('PREFLIGHT_PASS')
        if not args.execute:
            emit('DRY_RUN_COMPLETE')
            return 0
        consumed = state / (expected['identity']['RAINWRT_BUILD_ID'] + '.execute-started')
        private_write(consumed, str(run) + '\n')
        controller = Controller(transport, expected, baseline, emit)
        command = verify + final_memory_check + f'''[ "$(cat /proc/sys/kernel/random/boot_id)" = {baseline['boot_id']} ]
echo RAINWRT_SYSUPGRADE_INVOKED
exec /sbin/sysupgrade -f {remote}/config.tgz {remote_image}
'''
        attempted = True
        first = controller.execute(command)
        def finish_checks(p, phase):
            checks = required_checks(p, expected, baseline)
            for family, was_up in baseline_net.items():
                checks['HTTPS_DNS_' + family] = not was_up or network_check(transport, endpoints, family == 'ipv6')
            for service, digest in migration['enabled_custom_services'].items():
                # No service contents or names in public output.
                script = f'[ "$(sha256sum /etc/init.d/{service} | cut -d\' \' -f1)" = {digest} ] && find /etc/rc.d -name "S??{service}" | grep -q .\n'
                if transport.run(script).returncode:
                    checks['SERVICE_ENABLE_STATE_DRIFT'] = False
            for service in migration['disabled_services']:
                script = f'! find /etc/rc.d -name "S??{service}" | grep -q .\n'
                if transport.run(script).returncode:
                    checks['SERVICE_DISABLE_STATE_DRIFT'] = False
            emit(phase, checks)
            private_write(run / (phase + '.json'), json.dumps(p, indent=2))
            if not all(checks.values()):
                raise Stop('POSTCHECK_FAILED' if phase == 'first_boot' else 'REBOOT_VALIDATION_FAILED')
        finish_checks(first, 'first_boot')
        performance = transport.checked((ROOT / 'scripts/performance-audit.sh').read_text())
        private_write(run / 'performance.txt', performance)
        if args.validate_reboot:
            second = controller.reboot(first)
            finish_checks(second, 'second_boot')
        emit('HARDWARE_VALIDATED' if args.validate_reboot else 'FIRST_BOOT_VALIDATED')
        return 0
    except (Stop, OSError, ValueError, KeyError, subprocess.SubprocessError, tarfile.TarError) as e:
        message = str(e) if isinstance(e, Stop) else ('POSTCHECK_FAILED' if attempted else 'PRECHECK_FAILED') + ': local/transport/format error; private evidence retained'
        emit(message)
        if message == 'FAILED_TO_RETURN':
            emit('USE_VERIFIED_WEB_RECOVERY')
        emit('NO_FLASH_RETRY_NO_AUTOMATIC_RECOVERY')
        return 1
    finally:
        lock.close()


if __name__ == '__main__':
    sys.exit(main())
