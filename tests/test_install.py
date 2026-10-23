"""Installation must preflight both packages before making any device changes."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('pipboy_install', Path(__file__).resolve().parents[1] / 'scripts/install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class FakeDevice:
    def __init__(self, fail=None):
        self.events = []
        self.fail = fail

    def preflight(self, package, apk):
        self.events.append(('preflight', package))
        if package == self.fail:
            raise RuntimeError('signature mismatch')

    def snapshot(self):
        self.events.append(('snapshot',))

    def install(self, apk):
        self.events.append(('install', apk))


class InstallationTest(unittest.TestCase):
    def test_incompatible_second_package_never_installs_first(self):
        device = FakeDevice(fail='face')
        with self.assertRaises(RuntimeError):
            installer.install_all([('companion', 'c.apk'), ('face', 'f.apk')], device)
        self.assertEqual(device.events, [('preflight', 'companion'), ('preflight', 'face')])

    def test_snapshot_after_all_checks_before_any_install(self):
        device = FakeDevice()
        installer.install_all([('companion', 'c.apk'), ('face', 'f.apk')], device)
        self.assertEqual(device.events, [('preflight', 'companion'), ('preflight', 'face'),
                                        ('snapshot',), ('install', 'c.apk'), ('install', 'f.apk')])

    def test_downgrade_is_rejected(self):
        with self.assertRaises(ValueError):
            installer.check_versions(3, 2)

    def test_same_version_can_be_reinstalled(self):
        installer.check_versions(3, 3)

    def test_snapshot_failure_prevents_install(self):
        device = FakeDevice()
        def failed_snapshot():
            raise OSError('snapshot disk is full')
        device.snapshot = failed_snapshot
        with self.assertRaises(OSError):
            installer.install_all([('companion', 'c.apk'), ('face', 'f.apk')], device)
        self.assertTrue(all(event[0] == 'preflight' for event in device.events))

    def test_first_install_failure_stops_before_second(self):
        device = FakeDevice()
        def failed_install(apk):
            device.events.append(('install', apk))
            raise RuntimeError('device offline')
        device.install = failed_install
        with self.assertRaises(RuntimeError):
            installer.install_all([('companion', 'c.apk'), ('face', 'f.apk')], device)
        self.assertNotIn(('install', 'f.apk'), device.events)
