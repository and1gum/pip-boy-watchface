# Troubleshooting

[Українською](troubleshooting.uk.md) · [Installation](install.md) · [Data and limitations](data-sources.md)

## Compass is blank or does not resume

1. Wake and unlock the watch. The compass is intentionally hidden in AOD and while locked.
2. Confirm **Pip-Boy Compass** is installed and selected as the compass source in the face editor.
3. Open the companion once and press **Enable compass** if tracking is disabled. A force-stop requires opening it again. After unlocking, allow up to ten seconds for recovery.
4. Move away from magnets or a charger. Unreliable or stale sensor readings are hidden rather than shown as north.

Some Samsung watches can freeze the companion in the background despite its foreground service. If the compass works after opening the app but repeatedly fails after wrist-raise, try a battery optimization exemption for this package through ADB:

```sh
adb -s WATCH_IP:CONNECT_PORT shell cmd deviceidle whitelist +ua.and1gum.pipboy.compass
```

Check it with:

```sh
adb -s WATCH_IP:CONNECT_PORT shell cmd deviceidle whitelist
```

This helped on the tested SM-L715F. It does not keep the screen awake or run compass sensors in AOD. Battery impact has not been measured in a controlled comparison. This is a watch setting: reinstalling an APK or checking out source does not restore it. To remove the exemption:

```sh
adb -s WATCH_IP:CONNECT_PORT shell cmd deviceidle whitelist -ua.and1gum.pipboy.compass
```

If the issue persists, use [optional diagnostics](companion-diagnostics.md). A foreground service alone does not prove that headings reach the face.

## Weather is missing or shows an error

1. Open Samsung Weather, check that it has current data, and complete its location and permission setup.
2. Switch to another installed watch face, then switch back to Pip-Boy. This can restore a stuck system weather request, including after an APK update.
3. Allow the provider time to refresh. Opening Weather or reselecting Pip-Boy alone may not restore it.

The face receives weather from Wear OS. It cannot force an hourly refresh or repair the system provider. Switching faces is a recovery workaround, not a guarantee of automatic recovery. Dashes indicate missing values; the error marker reflects a provider error.

## Sunrise or sunset is missing or wrong

Enable location on the watch. Grant the companion approximate location and background location (**Allow all the time**). Tap sunrise or sunset and press **Оновити місце** (Update location). Check the watch's date and time zone.

If a fresh location is unavailable, the companion may use a saved position. After travel, update it again. Polar days or nights may have no sunrise or sunset.

## Phone battery is missing

Install [Phone Battery Complication](https://play.google.com/store/apps/details?id=com.weartools.phonebattcomp&hl=en) on both phone and watch and complete its setup. If necessary, select its **RANGED_VALUE** source in the face editor. It is a separate app, not bundled with Pip-Boy.

## Calendar is empty

Check that the watch's calendar provider has calendar access and an upcoming event. Select the system next-event source in the face editor if it was changed. **NO UPCOMING EVENTS** means the provider reported no event; **CALENDAR UNAVAILABLE** means it supplied no usable data.

## ADB cannot connect

Keep the watch awake and read the current address and connect port from **Wireless debugging**. The pairing port is different and is only used with `adb pair`. Ports can change. If authorization fails, open **Pair device with pairing code** and pair again, then connect using the port on the main screen.

## APK update fails

Use APKs signed with the same key as the installed packages. An `INSTALL_FAILED_UPDATE_INCOMPATIBLE` error can indicate a signing-key mismatch. Uninstalling removes local settings, saved location and pressure history; it also requires setting up the companion again. Use the original signing key when available.

The current companion does not request notification permission. No ADB notification-hiding command is needed after a fresh install. Older checkpoint APKs may still show the compass service notification. Android may separately list the current service among active apps.
