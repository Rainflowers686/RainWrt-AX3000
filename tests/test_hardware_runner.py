#!/usr/bin/env python3
"""Non-destructive transport/state/migration tests; never connects to hardware."""
import copy
import importlib.util
import io
import pathlib
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock
import contextlib
import json
import os

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runner', ROOT / 'scripts/hardware_test.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
EXPECTED = {'kernel': '6.12.103', 'identity': {'RAINWRT_UPSTREAM_VERSION': '25.12.2', 'RAINWRT_BUILD_ID': 'fixture'}}
GOOD = {
    'board': 'redmi,ax3000', 'kernel': '6.12.103', 'identity': EXPECTED['identity'],
    'release': {'release': '25.12.2', 'revision': 'fixture', 'target': 'qualcommax/ipq50xx'},
    'mtd': 'mtd1: 00080000 00020000 "0:MIBIB"\nmtd12: 00140000 00020000 "0:APPSBL"\nmtd18: 07480000 00020000 "rootfs"',
    'mibib': r.MIBIB, 'appsbl': r.APPSBL, 'char': True, 'cmdline': True, 'offset': 0xa80000,
    'bootcmd': 'bootmiwifi', 'boot_id': 'new', 'uptime': 150, 'mem_kib': 40000, 'tmp_kib': 50000, 'stage2_kib': 4000,
    'ubi': 'kernel rootfs rootfs_data', 'ubi_mtd': 18, 'mounts': '/ overlay overlayfs:/overlay\n/overlay ubifs /dev/ubi0_2',
    'fatal': False, 'phy': '/soc/c000000.wifi /soc/wifi1', 'bdf': '0x10 0x60',
    'rproc': 'running running running', 'bands': '1 1', 'wifi': [{'disabled': False, 'up': True, 'pending': False}] * 2,
    'ports': 'wan lan1 lan2 lan3 br-lan', 'carrier': True, 'wg': True, 'wg_abi': '6.12.103', 'apk': True,
    'ipv4': True, 'ipv6': True, 'resolver': True,
}
OLD = copy.deepcopy(GOOD)
OLD.update(kernel='6.6.137', identity={}, boot_id='old')
OLD['release'] = {'release': '24.10-SNAPSHOT', 'revision': 'r0-2b3c0919', 'target': 'qualcommax/ipq50xx'}


class Fake:
    def __init__(self, probes, code=246, message='Commencing upgrade. Closing all shell sessions.'):
        self.probes = iter(probes)
        self.commands = []
        self.code, self.message, self.now = code, message, 0

    def run(self, command, timeout=0):
        self.commands.append(command)
        return subprocess.CompletedProcess([], self.code, self.message.encode(), b'Connection failed')

    def probe(self):
        p = next(self.probes, r.Stop('offline'))
        if isinstance(p, Exception):
            raise p
        return copy.deepcopy(p)

    def sleep(self, duration):
        self.now += duration

    def controller(self):
        return r.Controller(self, EXPECTED, OLD, lambda *a: None, lambda: self.now, self.sleep)


class RunnerTests(unittest.TestCase):
    def test_all_required_pass(self):
        self.assertTrue(all(r.required_checks(GOOD, EXPECTED, OLD).values()))

    def test_required_failure_matrix(self):
        cases = {'wrong_board': ('board', 'other'), 'wrong_MTD': ('mtd', ''),
                 'wrong_MIBIB': ('mibib', 'bad'), 'wrong_APPSBL': ('appsbl', 'bad'),
                 'wrong_bootcmd': ('bootcmd', 'other'), 'wrong_size_offset': ('offset', 0),
                 'non_character': ('char', False), 'wrong_build': ('identity', {}),
                 'kernel_mismatch': ('kernel', '6.6.137'), 'UBI_failure': ('ubi', 'rootfs'),
                 'WireGuard_missing': ('wg', False), 'WireGuard_ABI': ('wg_abi', 'other'),
                 'APK_missing': ('apk', False), 'IPQ5018_failure': ('bdf', '0x60'),
                 'QCN6122_failure': ('rproc', 'running crashed'), 'wireless_failure': ('bands', '1 0'),
                 'network_failure': ('ipv4', False), 'IPv6_regression': ('ipv6', False),
                 'fatal_driver': ('fatal', True), 'Ethernet_failure': ('carrier', False),
                 'root_mount_failure': ('mounts', '/ tmpfs rootfs')}
        for name, (field, value) in cases.items():
            with self.subTest(name=name):
                p = copy.deepcopy(GOOD)
                p[field] = value
                self.assertFalse(all(r.required_checks(p, EXPECTED, OLD).values()))

    def test_user_disabled_wifi_is_allowed(self):
        p = copy.deepcopy(GOOD)
        p['wifi'] = [{'disabled': True, 'up': False, 'pending': False}] * 2
        self.assertTrue(r.required_checks(p, EXPECTED, OLD)['wireless'])

    def test_preflight_failure_never_writes(self):
        fake = Fake([GOOD])
        bad = dict(OLD, mibib='wrong')
        if all(r.layout_checks(bad).values()):
            fake.controller().execute('sysupgrade')
        self.assertEqual(fake.commands, [])

    def test_before_handoff_failure(self):
        fake = Fake([GOOD], 1, 'Image check failed')
        controller = fake.controller()
        with self.assertRaisesRegex(r.Stop, 'PRE_HANDOFF_FAILURE'):
            controller.execute('sysupgrade')
        with self.assertRaisesRegex(r.Stop, 'REFUSING_SECOND_SYSUPGRADE'):
            controller.execute('sysupgrade')
        self.assertEqual(len(fake.commands), 1)

    def test_persistent_attempt_marker_is_exclusive_and_not_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = pathlib.Path(tmp) / 'fixture.execute-started'
            r.private_write(marker, 'first-attempt\n')
            with self.assertRaises(FileExistsError):
                r.private_write(marker, 'second-attempt\n')
            self.assertEqual(marker.read_text(), 'first-attempt\n')

    def test_246_disconnect_new_system(self):
        fake = Fake([OLD, r.Stop('offline'), GOOD])
        control = fake.controller()
        self.assertEqual(control.execute('sysupgrade')['boot_id'], 'new')
        with self.assertRaisesRegex(r.Stop, 'REFUSING_SECOND'):
            control.execute('sysupgrade')
        self.assertEqual(len(fake.commands), 1)

    def test_missing_handoff_marker_indeterminate(self):
        self.assertEqual(r.handoff_state(255, ''), 'INDETERMINATE_HANDOFF')

    def test_timeout(self):
        fake = Fake([])
        with self.assertRaisesRegex(r.Stop, 'FAILED_TO_RETURN'):
            fake.controller().execute('sysupgrade')
        self.assertEqual(len(fake.commands), 1)

    def test_returned_old_and_wrong_build(self):
        for p, verdict in [(dict(OLD, boot_id='rebooted-old'), 'RETURNED_OLD_SYSTEM'),
                           (dict(GOOD, identity={'wrong': 'build'}), 'RETURNED_WRONG_BUILD')]:
            with self.subTest(verdict=verdict):
                with self.assertRaisesRegex(r.Stop, verdict):
                    Fake([p]).controller().execute('sysupgrade')

    def test_postcheck_failure_prevents_reboot(self):
        fake = Fake([dict(GOOD, apk=False)])
        with self.assertRaisesRegex(r.Stop, 'POSTCHECK_FAILED'):
            fake.controller().execute('sysupgrade')
        self.assertEqual(fake.commands, ['sysupgrade'])

    def test_normal_reboot_and_second_boot(self):
        fake = Fake([GOOD, dict(GOOD, boot_id='second')])
        control = fake.controller()
        first = control.execute('sysupgrade')
        self.assertEqual(control.reboot(first)['boot_id'], 'second')
        self.assertEqual(fake.commands, ['sysupgrade', 'sync\nreboot\n'])
        with self.assertRaisesRegex(r.Stop, 'REFUSING_UNSAFE_OR_SECOND_REBOOT'):
            control.reboot(first)

    def test_reboot_failure_and_identity_mismatch(self):
        for probes in ([], [dict(GOOD, boot_id='second', identity={})]):
            with self.subTest(probes=bool(probes)):
                with self.assertRaisesRegex(r.Stop, 'REBOOT_VALIDATION_FAILED'):
                    Fake(probes).controller().reboot(GOOD)

    def test_host_key_change_never_accepted(self):
        with self.assertRaisesRegex(r.Stop, 'SSH_HOST_KEY_CHANGED'):
            Fake([r.Stop('SSH_HOST_KEY_CHANGED')]).controller().execute('sysupgrade')

    def test_resource_budget_measured_not_tmpfs_only(self):
        reserve = r.reserve_kib(GOOD, 1024 * 1024)
        self.assertEqual(reserve, 8000 + 8192 + 2048)
        for mem, tmp in ((1, 50000), (50000, 1)):
            self.assertFalse(mem >= reserve and tmp >= reserve)
        with self.assertRaises(r.Stop):
            r.reserve_kib(dict(GOOD, stage2_kib=0))

    def resource_wait(self, values, passes, expected_time):
        now, samples, events = [0], iter(values), []
        def sample(timeout):
            self.assertLessEqual(timeout, 10)
            mem, tmp = next(samples)
            return {'mem_kib': mem, 'tmp_kib': tmp}
        def sleep(seconds):
            now[0] += seconds
        args = (sample, 18000, 16000, lambda *event: events.append(event), 'fixture')
        kwargs = {'clock': lambda: now[0], 'sleep': sleep}
        if passes:
            result = r.wait_resources(*args, **kwargs)
            self.assertGreaterEqual(result['mem_kib'], 34000)
            self.assertGreaterEqual(result['tmp_kib'], 34000)
            self.assertEqual(events[-1][0], 'RESOURCE_PASS')
        else:
            with self.assertRaisesRegex(r.Stop, 'PRECHECK_FAILED: resource stability timeout'):
                r.wait_resources(*args, **kwargs)
        self.assertEqual(now[0], expected_time)

    def test_resource_immediate_pass_still_needs_second_sample(self):
        self.resource_wait([(34000, 34000)] * 2, True, 5)

    def test_resource_transient_low_then_stable_pass(self):
        self.resource_wait([(10000, 50000), (50000, 10000), (34000, 34000), (35000, 35000)], True, 15)

    def test_resource_oscillating_never_two_consecutive(self):
        self.resource_wait([(35000, 35000), (33999, 50000)] * 12, False, 120)

    def test_resource_timeout_low_memory(self):
        self.resource_wait([(14000, 90000)] * 24, False, 120)

    def test_resource_sampler_time_counts_towards_deadline(self):
        now = [0]
        def sample(timeout):
            now[0] += 120
            return {'mem_kib': 50000, 'tmp_kib': 50000}
        with self.assertRaisesRegex(r.Stop, 'resource stability timeout'):
            r.wait_resources(sample, 18000, 16000, lambda *a: None, 'fixture',
                             clock=lambda: now[0], sleep=lambda _: self.fail('past deadline'))

    def test_archive_integrity_core_keys_and_stale_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = pathlib.Path(tmp) / 'in.tgz', pathlib.Path(tmp) / 'out.tgz'
            with tarfile.open(src, 'w:gz') as archive:
                for name in [*['etc/config/' + n for n in ('network', 'wireless', 'dhcp', 'firewall', 'system')],
                             'etc/dropbear/dropbear_test_host_key', 'etc/rc.d/S01fixture', 'etc/apk/repositories',
                             'etc/opkg/distfeeds.conf', 'lib/upgrade/platform.sh']:
                    info = tarfile.TarInfo(name)
                    info.size = 7
                    archive.addfile(info, io.BytesIO(b'fixture'))
            r.migrate_archive(src, dst, set())
            audit = r.audit_archive(src, dst)
            self.assertTrue(all(audit.values()))
            self.assertEqual(audit['core_config_count'], 5)
            self.assertEqual(audit['SSH_host_key_count'], 1)
            data = bytearray(dst.read_bytes())
            data[-8] ^= 1
            dst.write_bytes(data)
            with self.assertRaises(OSError):
                r.audit_archive(src, dst)

    def test_opaque_archive_filters_and_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = pathlib.Path(tmp) / 'in.tgz', pathlib.Path(tmp) / 'out.tgz'
            with tarfile.open(src, 'w:gz') as archive:
                for name in ('etc/config/network', 'etc/init.d/user-service', 'etc/init.d/disabled-service',
                             'etc/opkg/distfeeds.conf', 'lib/upgrade/platform.sh', 'lib/apk/db/installed'):
                    info = tarfile.TarInfo(name)
                    data = b'opaque-test-fixture\n'
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
            result = r.migrate_archive(src, dst, {'user-service', 'missing-service'})
            self.assertEqual(result['removed_members'], 3)
            self.assertEqual(set(result['enabled_custom_services']), {'user-service'})
            with tarfile.open(dst) as archive:
                names = archive.getnames()
                self.assertNotIn('etc/opkg/distfeeds.conf', names)
                script = archive.extractfile('etc/uci-defaults/91-rainwrt-preserved-services').read().decode()
                self.assertIn('/etc/init.d/user-service enable', script)
                self.assertNotIn('missing-service', script)
                self.assertNotIn('disabled-service enable', script)
                subprocess.run(['sh', '-n'], input=script.encode(), check=True)

    def test_unsafe_archive_and_shell_injection_rejected(self):
        for name in ('../escape', 'etc/init.d/evil;command', 'etc/init.d/a\ncommand'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                src, dst = pathlib.Path(tmp) / 'in.tgz', pathlib.Path(tmp) / 'out.tgz'
                with tarfile.open(src, 'w:gz') as archive:
                    info = tarfile.TarInfo(name)
                    info.size = 1
                    archive.addfile(info, io.BytesIO(b'x'))
                with self.assertRaises(r.Stop):
                    r.migrate_archive(src, dst, set())

    def test_disabled_state_is_parsed_not_executed(self):
        for data, valid in ((b'/etc/init.d/disabled-service disable\n\nexit 0\n', True),
                            (b'/etc/init.d/evil;command disable\n', False)):
            with self.subTest(valid=valid), tempfile.TemporaryDirectory() as tmp:
                src, dst = pathlib.Path(tmp) / 'in.tgz', pathlib.Path(tmp) / 'out.tgz'
                with tarfile.open(src, 'w:gz') as archive:
                    info = tarfile.TarInfo('/etc/uci-defaults/10_disable_services')
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
                if not valid:
                    with self.assertRaises(r.Stop):
                        r.migrate_archive(src, dst, set())
                    continue
                result = r.migrate_archive(src, dst, set())
                self.assertEqual(result['disabled_services'], ['disabled-service'])
                with tarfile.open(dst) as archive:
                    script = archive.extractfile('etc/uci-defaults/91-rainwrt-preserved-services').read()
                    subprocess.run(['sh', '-n'], input=script, check=True)

    def test_main_wrong_manifest_or_image_never_connects(self):
        for bad_anchor in (True, False):
            with self.subTest(bad_anchor=bad_anchor), tempfile.TemporaryDirectory() as directory:
                base = pathlib.Path(directory)
                state = base / 'rainwrt'
                state.mkdir()
                candidate = base / 'candidate'
                candidate.mkdir()
                (candidate / 'image.bin').write_bytes(b'fixture')
                manifest = candidate / 'candidate.json'
                manifest.write_text(json.dumps({'files': {'image.bin': 'wrong-hash'}}))
                (state / 'hardware-test.json').write_text(json.dumps({'candidate_dir': str(candidate),
                    'manifest_sha256': 'wrong' if bad_anchor else r.sha(manifest)}))
                with mock.patch.dict(os.environ, {'XDG_STATE_HOME': str(base)}), \
                     mock.patch('sys.argv', ['runner']), mock.patch.object(r, 'Transport') as transport, \
                     mock.patch.object(r.shutil, 'which', return_value='/bin/true'), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(r.main(), 1)
                    transport.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
