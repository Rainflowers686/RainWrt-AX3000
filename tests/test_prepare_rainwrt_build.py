#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'prepare_rainwrt_build', ROOT / 'scripts/prepare-rainwrt-build.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PinnedVersionTests(unittest.TestCase):
    def test_immortalwrt_fallback_with_config_override_is_valid(self):
        version = (
            'VERSION_NUMBER:=$(call qstrip,$(CONFIG_VERSION_NUMBER))\n'
            'VERSION_NUMBER:=$(if $(VERSION_NUMBER),$(VERSION_NUMBER),25.12.2)\n')
        self.assertTrue(MODULE.matches_pinned_version(version))

    def test_wrong_release_fallback_is_rejected(self):
        version = 'VERSION_NUMBER:=$(if $(VERSION_NUMBER),$(VERSION_NUMBER),25.12.3)\n'
        self.assertFalse(MODULE.matches_pinned_version(version))

    def test_missing_version_assignment_is_rejected(self):
        self.assertFalse(MODULE.matches_pinned_version('VERSION_CODE:=r1\n'))

    def test_later_unpinned_override_is_rejected(self):
        version = (
            'VERSION_NUMBER:=$(if $(VERSION_NUMBER),$(VERSION_NUMBER),25.12.2)\n'
            'VERSION_NUMBER:=development\n')
        self.assertFalse(MODULE.matches_pinned_version(version))


if __name__ == '__main__':
    unittest.main()
