# Developer guide

[Project overview](../README.md) · [Data and limitations](data-sources.md) · [Diagnostics](companion-diagnostics.md)

## Build

Use JDK 17+, Android SDK platform 36 and build-tools 35.0.0, Python 3 with Pillow, and Node.js for the rendering/tests. Set `JAVA_HOME` and `ANDROID_HOME` if the tools are outside the local default path in `scripts/build.sh`.

```sh
python3 -m pip install Pillow
bash scripts/build.sh
```

The script generates the face, runs Python and companion Java tests, runs Android lint, and assembles both APKs:

- `artifacts/PipBoy-0.2.0-debug.apk`
- `artifacts/PipBoy-Compass-0.2.0-debug.apk`
- `artifacts/SHA256SUMS`

## Debug and release builds

`scripts/build.sh` invokes `assembleDebug` for both modules and copies the resulting APKs with the `-debug` suffix. The Gradle modules use the default debug build type: debugging is enabled and signing uses the local debug keystore. There is no configured release signing workflow. See [Android build types](https://developer.android.com/build/build-variants#build-types).

This is separate from the companion's optional diagnostics recorder, which is off on process start. A debug build does not automatically start that recording. Renaming an APK does not change its build type, signing key or debugging settings.

Preserve the signing key when distributing updates; a matching package/version name does not imply a matching signature. A release workflow needs signing configuration and its own validation, including any code optimization. Do not infer a battery improvement from a build-type change alone. Keep install instructions and artifact names in sync when changing versions.

## Source layout

| Path | Purpose |
| --- | --- |
| `scripts/generate.py` | Production layout, tap targets, generated resources and WFF XML |
| `watchface/src/main/res/raw/watchface.xml` | Generated face; regenerate instead of editing by hand |
| `compass/` | Compass, pressure, solar calculations and optional diagnostics |
| `tests/` | Generated layout, data expressions and tap-target checks |
| `compass/src/test/` | Heading, motion, lifecycle policy, diagnostics, pressure and solar unit tests |
| `scripts/render.py` | Illustrative previews using sample data |
| `licenses/` | Third-party font and library notices |

The face uses a 480 × 480 logical canvas. Hour and minute hands use generated PNG assets rotated by WFF time expressions. The final scene group draws hour, minute and second hands above the readouts and hides them in ambient mode. Calendar arcs wrap at word boundaries and truncate the final row. Geometry and clipping rules are covered by the layout tests.

Preserve complication slot IDs and declaration order across updates: changing them can disturb provider bindings. The numeric compass payload carries continuous degrees across north; text labels stay normalized to 000–359. The face counterrotates cardinal letters while rotating the rim and keeps hour marks fixed.

## Compass lifecycle

`CompassTrackingService` is a `specialUse` foreground service. Tracking requires an enabled companion, at least one assigned compass slot, `Display.STATE_ON`, and an unlocked keyguard. Do not replace the display-state gate with `PowerManager.isInteractive()`: Samsung wrist-raise can show the active face while that flag remains false. Android 36+ explicitly subscribes to display-state events.

Sleep, AOD and lock unregister the compass sensors, cancel motion updates, clear the reading and request `NoData`. The service remains available for wake events. A ten-second eligibility retry covers missing unlock events without holding a wake lock. `START_STICKY` requests process recovery; a boot/package-update receiver restarts an enabled, assigned provider. Android may delay a restart; force-stop requires opening the app again.

The manifest intentionally omits `POST_NOTIFICATIONS`. Keep the notification passed to `startForeground()` because Android requires it, while the missing permission prevents normal notification-list display. See [Android's notification permission contract](https://developer.android.com/develop/ui/views/notifications/notification-permission). The service may remain visible in the system's active-app list.

The public APIs do not report exact face visibility: sensors can remain active while another app is open on an unlocked, active display. Samsung background freezing may require the package-specific exemption described in [troubleshooting](troubleshooting.md#compass-is-blank-or-does-not-resume).

## Motion and provider updates

The sensor uses `SENSOR_DELAY_UI`, with a 100 ms circular filter and a 120 ms visual-motion filter. Display rotation changes reset the motion state. The software update gate is 33 ms; a change of at least 0.03° can request publication, with a four-second heartbeat for an unchanged heading. Readings must have at least LOW sensor accuracy and be younger than five seconds; payload validity is also five seconds.

`ComplicationDataSourceUpdateRequester` requests delivery through Wear OS; it does not guarantee the physical frame rate. Callback success and visible rendering are different checks. Keep [diagnostics](companion-diagnostics.md) disabled for normal use and battery comparisons. No measured battery-saving percentage is available.

## Verify changes

Run `bash scripts/build.sh` for production changes. Use the generated XML and tests to check active and ambient visibility, touch bounds, slot bindings and north crossings as relevant. Preview images use sample values and are not device evidence.

For lifecycle changes, check natural wrist-raise after AOD, lock/unlock and sensor shutdown on a real watch. Confirm active and ambient modes separately; a successful build or install does not establish provider recovery. For battery comparisons, disconnect ADB/debuggers and keep brightness, AOD, connectivity and battery-exemption settings comparable.

Keep user-facing instructions in English and Ukrainian. Describe current behavior; use Git history and release tags for past experiments and checkpoints.
