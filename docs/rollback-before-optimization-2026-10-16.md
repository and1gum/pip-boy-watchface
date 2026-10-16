# Checkpoint before companion optimization

Tag: `checkpoint/pre-optimization-2026-10-16`.

The corresponding GitHub release preserves both debug APKs and SHA256SUMS.
The source includes the wrist-raise display policy, explicit display-state
subscription and analysis. Build/lint plus 50 Python and 19 Java tests passed.
The observed device baseline was three successful natural wrist-raises after
78 seconds of AOD, with first delivered data around 0.46 s after each gesture.
This is not an overnight battery or reboot-recovery guarantee.

## Restore the APKs

Download the APKs and SHA256SUMS from this tag's release and verify their hashes.
Use the current watch endpoint from Wireless debugging:

```sh
adb -s WATCH_IP:CONNECT_PORT install --no-streaming -r PipBoy-0.2.0-debug.apk
adb -s WATCH_IP:CONNECT_PORT install --no-streaming -r PipBoy-Compass-0.2.0-debug.apk
```

Future higher version codes may require the explicit downgrade option `-d` for
these debug packages. Preserve app data; do not uninstall merely to downgrade.
A different signing key cannot update these APKs in place.

## Device state outside Git

The tested watch uses a user battery exemption for only the companion:

```sh
adb -s WATCH_IP:CONNECT_PORT shell cmd deviceidle whitelist +ua.and1gum.pipboy.compass
```

Git checkout and APK installation do not restore this system setting. Confirm it
in `dumpsys deviceidle whitelist`. Before the trial, the package was absent; undo
with the same command using `-ua.and1gum.pipboy.compass` if required. Sensor
sampling still pauses in AOD. Do not disable the global Samsung freezer.

## Inspect checkpoint source without overwriting later work

```sh
git fetch origin --tags
git worktree add --detach ../pip-boy-checkpoint checkpoint/pre-optimization-2026-10-16
```

No live location/preferences or personal calendar data is included in the release.
