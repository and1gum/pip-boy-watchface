# Install Pip-Boy on a watch

The primary variant is **0.3.0 release**, signed with the project's permanent release key. The face's previous debug variant was tested on Samsung Galaxy Watch Ultra2 (2026; SM-L715F), Wear OS 7. The debug-to-release migration, existing configuration and active/natural AOD were verified on that watch with Android 17 (API 37). You need a computer, the watch and network access between them.

[Українською](install.uk.md) · [Troubleshooting](troubleshooting.md)

## 1. Install the phone battery provider

To show your phone's battery on the face:

1. Install [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp&hl=en) from Google Play on your phone.
2. Install the same app on your watch: select the watch in Google Play's device list, or find **Phone Battery Complication** in the watch's Play Store.
3. Open the app once **on both phone and watch** and complete its initial setup. Keep the phone and watch connected to each other.

Do this before selecting Pip-Boy so the battery source can bind automatically. This third-party app is not bundled with either Pip-Boy APK. If you do not need phone battery, skip this step; its field will remain empty.

## 2. Obtain the two APKs

Download `PipBoy-Compass-0.3.0-release.apk`, `PipBoy-0.3.0-release.apk` and `SHA256SUMS` from [GitHub Releases](https://github.com/and1gum/pip-boy-watchface/releases). Put them in `artifacts/release/` in a checkout of the matching source tag, then verify:

```bash
(cd artifacts/release && sha256sum -c SHA256SUMS)
```

To build from source, install JDK 17+, Android SDK platform 36/build-tools 35.0.0, Python 3 with Pillow and Node.js. Set `JAVA_HOME` and `ANDROID_HOME`. Configure the [permanent signing key](release-signing.md) once, then:

```bash
bash scripts/build-release.sh
```

For debugging, `bash scripts/build.sh` writes `artifacts/PipBoy-Compass-0.3.0-debug.apk` and `artifacts/PipBoy-0.3.0-debug.apk`, with `artifacts/SHA256SUMS`. Debug is signed with your local debug key and is not a downgrade path from release. Diagnostics recording is off by default in both variants.

## 3. Pair wireless ADB

On the watch, enable **Developer options** and **Wireless debugging**. Open **Pair device with pairing code** and note its IP address, **pairing port**, and code. On the computer:

```bash
adb pair WATCH_IP:PAIR_PORT
```

Enter the code shown on the watch. Return to the main Wireless debugging screen and note its **connect port**. This is usually a different port and can change later:

```bash
adb connect WATCH_IP:CONNECT_PORT
adb devices
```

`adb devices` should list the watch. Substitute the actual address and ports; do not type the placeholder words. If your computer uses Windows ADB from WSL, run `adb.exe` and pass APK paths converted with `wslpath -w`.

## 4. Install and select the face

Use the checked installer from the matching source checkout:

```bash
bash scripts/install-release.sh --serial WATCH_IP:CONNECT_PORT
```

It verifies both packages, version codes and signing certificates (including the authenticated debug-to-release rotation) before installing either APK. It saves previous APKs, available debug preferences, a screenshot and system dumps under `~/.local/state/pip-boy/backups/`, then installs the companion and face with `install -r`. These files are an audit snapshot, not an automatic restore of Wear OS configuration. It never uninstalls or clears data. For Windows ADB in WSL add `--adb /absolute/path/to/adb.exe`; APK paths are converted automatically.

For an existing Pip-Boy installation, leave the current face selected and check that its customized heart-rate boundaries, complication providers and permissions remain after updating. Do not remove the face first. If a signature check fails, stop and read [signing and migration](release-signing.md).

For a fresh installation, select **Pip-Boy** in the watch-face picker after both APKs report `Success`. Reopen the picker if needed.

To install the debug variant on a compatible debug installation or a clean device:

```bash
bash scripts/install-debug.sh --serial WATCH_IP:CONNECT_PORT
```

## 5. Check data sources

The data sources are preset; no separate configuration file is needed. When the companion and Phone Battery Complication are installed before selecting the face, Wear OS should bind them automatically. Open **Customize / Edit** only if a field is empty or was changed previously. The preset sources are:

| Face area | Source | Value type |
| --- | --- | --- |
| Upper calendar arc | System next calendar event | LONG_TEXT |
| Phone battery | [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp&hl=en) | RANGED_VALUE |
| Compass rim | Pip-Boy Compass | RANGED_VALUE |
| Pressure | Pip-Boy Barometer | RANGED_VALUE |
| Sunrise and sunset | Pip-Boy Sunrise and Sunset | SHORT_TEXT |

The same solar provider supplies both sunrise and sunset slots. Weather, steps, heart rate and watch battery use the watch's own data; availability depends on its providers and permissions. If you skipped step 1, leave the phone battery slot empty.

Open **Pip-Boy Compass** in the watch's app list once after assigning the compass. It then restarts automatically after a watch reboot or companion update, provided tracking is enabled and the compass slot remains assigned. Its **Stop compass / Enable compass** button controls tracking. The sensor pauses when the display sleeps, enters ambient mode, or locks, and may take up to ten seconds to resume after unlocking. Wrist-raise activation is supported. Its reading is magnetic heading, so it can differ from true north.

To show sunrise and sunset, allow location services on the watch, grant the companion approximate location and **Allow all the time** background location in the watch's app permissions, then tap a solar time on the face. This opens a small screen that fetches the watch's location; use **Update location** if needed. Without a current location the last saved position may be used, or the values may be unavailable.

## Permissions and privacy

The watch-face APK has no Android runtime permissions. The companion requests foreground-service permissions to keep its compass provider available while the display is ON and unlocked, permission to restart it after boot, and approximate plus background location for periodic sunrise/sunset updates. Android may prompt for runtime permissions separately. The companion does not request notification permission, so its compass service notification stays out of the notification list, including after a fresh install. Android may still list the service among active apps.

Compass, pressure and location are read on the watch. The companion saves the last location and a short pressure history locally. The project has no account, analytics, or project-operated server. The watch's system location and weather providers may use their own network services under their own settings. The source code is available here for inspection.

## Updates and help

For subsequent updates use `bash scripts/install-release.sh --serial WATCH_IP:CONNECT_PORT` with the matching release source and APKs. Preserve the release key and signing lineage. Old debug checkpoint APKs cannot replace a release installation in place. Uninstalling, clearing data or resetting the watch loses settings; this migration workflow does none of those.

For missing weather, compass, calendar or battery data, see [troubleshooting](troubleshooting.md). [Optional diagnostics](companion-diagnostics.md) can help capture a compass problem.
