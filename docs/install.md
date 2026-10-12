# Install Pip-Boy on a watch

This guide installs the current **0.2.0 debug build** from source. It was tested on Samsung Galaxy Watch Ultra2 (2026; model SM-L715F) with Wear OS 7. Menus may differ on another watch. You need a computer, the watch, and a network path between them; the computer can use Ethernet.

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

Both commands must print `Success`. Choose **Pip-Boy** from the watch's face picker. If it does not appear immediately, reopen the picker. For the tested watch, the optional ADB selection command is:

```bash
adb -s WATCH_IP:CONNECT_PORT shell am broadcast \
  -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface --es watchFaceId ua.and1gum.pipboy
```

The broadcast is a debug shortcut; use the face picker for normal selection.

## 4. Check data sources

No separate configuration file is needed: the default sources are built into `watchface.xml` inside the APK. When the companion and Phone Battery Complication are installed before selecting the face, Wear OS should bind them automatically. Open **Customize / Edit** only if a field is empty or was changed previously. The preset sources are:

| Face area | Source | Value type |
| --- | --- | --- |
| Upper calendar arc | System next calendar event | LONG_TEXT |
| Phone battery | [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp&hl=en) | RANGED_VALUE |
| Compass rim | Pip-Boy Compass | RANGED_VALUE |
| Pressure | Pip-Boy Barometer | RANGED_VALUE |
| Sunrise and sunset | Pip-Boy Sunrise and Sunset | SHORT_TEXT |

On the tested watch, Samsung Barometer provides only `SHORT_TEXT` and `LONG_TEXT`. The numeric column needs `RANGED_VALUE`, so our provider reads the same watch pressure sensor and adds a trend based on a short local history.

The same solar provider supplies both sunrise and sunset slots. Weather, steps, heart rate and watch battery use the watch's own data; availability depends on its providers and permissions. The linked phone-battery provider is **not included**: install its phone and watch apps first. If you do not use it, leave that slot empty.

Open **Pip-Boy Compass** in the watch's app list once after assigning the compass. It then restarts automatically after a watch reboot or companion update, provided tracking is enabled and the compass slot remains assigned. Its **Stop compass / Enable compass** button controls tracking. The sensor pauses when the display sleeps, enters ambient mode, or locks, and may take up to ten seconds to resume after unlocking. Its reading is magnetic heading, so it can differ from true north.

To show sunrise and sunset, allow location services on the watch, grant the companion approximate location and **Allow all the time** background location in the watch's app permissions, then tap a solar time on the face. This opens a small screen that fetches the watch's location; use **Update location** if needed. Without a current location the last saved position may be used, or the values may be unavailable.

## Permissions and privacy

The watch-face APK has no Android runtime permissions. The companion requests foreground-service permissions to keep its compass provider available while the interactive display is unlocked, permission to restart it after boot, notification permission for that foreground service, and approximate plus background location for periodic sunrise/sunset updates. Android may prompt for runtime permissions separately.

Compass, pressure and location are read on the watch. The companion saves the last location and a short pressure history locally. The project has no account, analytics, or project-operated server. The watch's system location and weather providers may use their own network services under their own settings. The source code is available here for inspection.

## Troubleshooting

- **ADB cannot connect:** check that the watch and computer can reach each other, then read the *current* connect port from Wireless debugging. Pairing and connect ports are different.
- **Compass is blank:** confirm that the companion is installed. If the source was not selected automatically, choose Pip-Boy Compass in the editor. Open its app once, press **Enable compass** if needed, and wake/unlock the display. An invalid or stale sensor reading is intentionally hidden.
- **No solar time:** turn on watch location, check approximate and background permissions for the companion, then tap a solar time or reopen its location screen.
- **No phone battery:** install Phone Battery Complication on the phone and watch. If the slot stays empty, choose its RANGED_VALUE source in the editor.
- **Weather is blank after switching faces:** return to Pip-Boy and allow the watch's weather provider time to refresh. Check its own setup and permissions.
- **An update fails with a signature error:** debug builds from different machines have different signing keys. Uninstalling the old package and reinstalling removes its local settings; save anything you need first.
