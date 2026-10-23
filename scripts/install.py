#!/usr/bin/env python3
"""Check both APK updates before installing; never uninstall or clear watch data."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ('ua.and1gum.pipboy.compass', 'ua.and1gum.pipboy')


def check_versions(installed, incoming):
    if incoming < installed:
        raise ValueError(f'Version downgrade refused: installed={installed}, incoming={incoming}')


def install_all(plan, device):
    for package, apk in plan:
        device.preflight(package, apk)
    device.snapshot()
    for _, apk in plan:
        device.install(apk)


class Device:
    def __init__(self, adb, serial, sdk_dir, work, backup_root):
        self.adb, self.serial = adb, serial
        self.sdk_dir, self.work = Path(sdk_dir), Path(work)
        self.tools = self.sdk_dir / 'build-tools/35.0.0'
        self.backup_root = Path(backup_root).expanduser()
        self.previous = []
        self.sdk = int(self.command('shell', 'getprop', 'ro.build.version.sdk').stdout.strip())
        if self.sdk < 35:
            raise ValueError('Pip-Boy requires Android SDK 35+')

    def command(self, *args, check=True):
        return subprocess.run([self.adb, '-s', self.serial, *map(str, args)],
                              check=check, capture_output=True)

    def adb_path(self, path):
        if self.adb.lower().endswith('.exe'):
            return subprocess.check_output(['wslpath', '-w', str(Path(path).resolve())], text=True).strip()
        return str(path)

    def metadata(self, apk):
        output = subprocess.check_output([str(self.tools / 'aapt'), 'dump', 'badging', str(apk)], text=True)
        match = re.search(r"package: name='([^']+)' versionCode='(\d+)'", output)
        if not match:
            raise ValueError(f'Cannot read package/version from {apk}')
        return match[1], int(match[2])

    def preflight(self, package, apk):
        name, incoming_version = self.metadata(apk)
        if name != package:
            raise ValueError(f'Expected {package}; found {name}')
        subprocess.run([str(self.tools / 'apksigner'), 'verify', str(apk)], check=True)
        result = self.command('shell', 'pm', 'path', package, check=False)
        output = result.stdout.decode().strip()
        if not output:
            # Distinguish an absent package from a failed shell/transport command.
            packages = self.command('shell', 'pm', 'list', 'packages', package).stdout.decode()
            if result.returncode not in (0, 1) or f'package:{package}' in packages:
                raise RuntimeError(f'Could not inspect installed package {package}: {result.stderr.decode()}')
            print(f'{package}: fresh installation')
            return
        paths = [line.removeprefix('package:').strip() for line in output.splitlines()]
        if len(paths) != 1 or not output.startswith('package:'):
            raise ValueError(f'Split APK or unexpected package layout for {package}; refusing update')
        old = self.work / f'{package}.apk'
        self.command('pull', paths[0], self.adb_path(old))
        old_package, old_version = self.metadata(old)
        if old_package != package:
            raise ValueError('Installed APK identity mismatch')
        check_versions(old_version, incoming_version)
        subprocess.run(['java', '--class-path', str(self.tools / 'lib/apksigner.jar'),
                        str(ROOT / 'scripts/ApkCompatibility.java'), str(old), str(apk), str(self.sdk)], check=True)
        self.previous.append((package, old, old_version))

    def snapshot(self):
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        self.backup = self.backup_root / stamp
        self.backup.mkdir(parents=True, mode=0o700)
        metadata = {'serial': self.serial, 'sdk': self.sdk, 'packages': [],
                    'note': 'Audit snapshot and prior APKs. System dumps are not a restorable Wear OS backup. No data is cleared.'}
        for package, old, version in self.previous:
            shutil.copy2(old, self.backup / old.name)
            metadata['packages'].append({'package': package, 'versionCode': version})
            dump = self.command('shell', 'dumpsys', 'package', package).stdout
            (self.backup / f'{package}.txt').write_bytes(dump)
            # Debug-only supplementary private-data archive; not used as a pretend WFF backup.
            prefs = self.command('exec-out', 'run-as', package, 'tar', '-cf', '-', 'shared_prefs', check=False)
            if prefs.returncode == 0 and prefs.stdout:
                (self.backup / f'{package}-debug-prefs.tar').write_bytes(prefs.stdout)
        (self.backup / 'wallpaper.txt').write_bytes(self.command('shell', 'dumpsys', 'wallpaper').stdout)
        screenshot = self.command('exec-out', 'screencap', '-p', check=False)
        if screenshot.returncode == 0:
            (self.backup / 'screen.png').write_bytes(screenshot.stdout)
        (self.backup / 'snapshot.json').write_text(json.dumps(metadata, indent=2) + '\n')
        print(f'Pre-update snapshot: {self.backup}', flush=True)

    def install(self, apk):
        result = self.command('install', '-r', self.adb_path(apk), check=False)
        output = result.stdout.decode() + result.stderr.decode()
        print(output.strip(), flush=True)
        if result.returncode != 0 or 'Success' not in output:
            raise RuntimeError('Installation did not report Success. No uninstall fallback will be attempted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', choices=('debug', 'release'))
    parser.add_argument('--serial', required=True, help='Explicit ADB device serial or IP:CONNECT_PORT')
    parser.add_argument('--adb', default=os.environ.get('ADB', str(Path(os.environ.get('ANDROID_HOME', '')) / 'platform-tools/adb')))
    parser.add_argument('--backup-dir', default=str(Path.home() / '.local/state/pip-boy/backups'))
    args = parser.parse_args()
    sdk_dir = os.environ.get('ANDROID_HOME')
    if not sdk_dir:
        parser.error('Set ANDROID_HOME or use scripts/install-debug.sh / scripts/install-release.sh')
    version = next(line.split('=', 1)[1] for line in (ROOT / 'gradle.properties').read_text().splitlines()
                   if line.startswith('pipboyVersionName='))
    folder = ROOT / 'artifacts' / ('release' if args.variant == 'release' else '')
    plan = [(PACKAGES[0], folder / f'PipBoy-Compass-{version}-{args.variant}.apk'),
            (PACKAGES[1], folder / f'PipBoy-{version}-{args.variant}.apk')]
    for _, apk in plan:
        if not apk.is_file():
            parser.error(f'Build first: missing {apk}')
    with tempfile.TemporaryDirectory(prefix='pipboy-preflight-') as work:
        device = Device(args.adb, args.serial, sdk_dir, work, args.backup_dir)
        install_all(plan, device)
    print('Both APK installations reported Success. Check existing configuration, providers, active mode and AOD on the watch.')


if __name__ == '__main__':
    main()
