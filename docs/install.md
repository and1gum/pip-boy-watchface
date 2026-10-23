# Install Pip-Boy on a watch

This guide installs the current **0.2.0 debug build** from source. It was tested on Samsung Galaxy Watch Ultra2 (2026; model SM-L715F) with Wear OS 7. Menus may differ on another watch. You need a computer, the watch, and a network path between them; the computer can use Ethernet.

[Українською](install.uk.md) · [Troubleshooting](troubleshooting.md)

## 1. Build the two APKs

Install JDK 17 or newer, Android SDK platform 36 and build-tools 35.0.0, Python 3 with Pillow, and Node.js. Set `JAVA_HOME` and `ANDROID_HOME` to your installations, then run from the repository root:

```bash
python3 -m pip install Pillow
bash scripts/build.sh
```

The script tests and builds both modules. It writes `artifacts/PipBoy-Compass-0.2.0-debug.apk` and `artifacts/PipBoy-0.2.0-debug.apk`. It also writes `SHA256SUMS` so you can check the files with `cd artifacts && sha256sum -c SHA256SUMS`.

## 2. Pair wireless ADB

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

## 3. Install and select the face

Install the companion first, then the face:

```bash
adb -s WATCH_IP:CONNECT_PORT install -r artifacts/PipBoy-Compass-0.2.0-debug.apk
adb -s WATCH_IP:CONNECT_PORT install -r artifacts/PipBoy-0.2.0-debug.apk
```

Both commands must print `Success`. Choose **Pip-Boy** from the watch's face picker. If it does not appear immediately, reopen the picker.

## 4. Check data sources

The data sources are preset; no separate configuration file is needed. When the companion and Phone Battery Complication are installed before selecting the face, Wear OS should bind them automatically. Open **Customize / Edit** only if a field is empty or was changed previously. The preset sources are:

| Face area | Source | Value type |
| --- | --- | --- |
| Upper calendar arc | System next calendar event | LONG_TEXT |
| Phone battery | [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp&hl=en) | RANGED_VALUE |
| Compass rim | Pip-Boy Compass | RANGED_VALUE |
| Pressure | Pip-Boy Barometer | RANGED_VALUE |
| Sunrise and sunset | Pip-Boy Sunrise and Sunset | SHORT_TEXT |

The same solar provider supplies both sunrise and sunset slots. Weather, steps, heart rate and watch battery use the watch's own data; availability depends on its providers and permissions. The linked phone-battery provider is **not included**: install its phone and watch apps first. If you do not use it, leave that slot empty.

Open **Pip-Boy Compass** in the watch's app list once after assigning the compass. It then restarts automatically after a watch reboot or companion update, provided tracking is enabled and the compass slot remains assigned. Its **Stop compass / Enable compass** button controls tracking. The sensor pauses when the display sleeps, enters ambient mode, or locks, and may take up to ten seconds to resume after unlocking. Wrist-raise activation is supported. Its reading is magnetic heading, so it can differ from true north.

To show sunrise and sunset, allow location services on the watch, grant the companion approximate location and **Allow all the time** background location in the watch's app permissions, then tap a solar time on the face. This opens a small screen that fetches the watch's location; use **Update location** if needed. Without a current location the last saved position may be used, or the values may be unavailable.

## Permissions and privacy

The watch-face APK has no Android runtime permissions. The companion requests foreground-service permissions to keep its compass provider available while the display is ON and unlocked, permission to restart it after boot, and approximate plus background location for periodic sunrise/sunset updates. Android may prompt for runtime permissions separately. The companion does not request notification permission, so its compass service notification stays out of the notification list, including after a fresh install. Android may still list the service among active apps.

Compass, pressure and location are read on the watch. The companion saves the last location and a short pressure history locally. The project has no account, analytics, or project-operated server. The watch's system location and weather providers may use their own network services under their own settings. The source code is available here for inspection.

## Updates and help

To update, rebuild from the desired source revision and repeat the two `install -r` commands. Keep the same signing key to preserve app settings. The older APKs in [GitHub Releases](https://github.com/and1gum/pip-boy-watchface/releases) are rollback checkpoints and may behave differently from the current source.

For missing weather, compass, calendar or battery data, see [troubleshooting](troubleshooting.md). [Optional diagnostics](companion-diagnostics.md) can help capture a compass problem.
