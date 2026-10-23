# Developer guide

[Project overview](../README.md) · [Data and limitations](data-sources.md) · [Diagnostics](companion-diagnostics.md)

## Build

Use JDK 17+, Android SDK platform 36/build-tools 35.0.0, Python 3 with Pillow, and Node.js. Set `JAVA_HOME` and `ANDROID_HOME` if needed; `scripts/toolchain.sh` retains the previous local defaults. Version name and code are shared through `pipboyVersionName` and `pipboyVersionCode` in `gradle.properties`.

## Debug and release builds

| Variant | Build | Install | Output |
| --- | --- | --- | --- |
| **Release (primary)** | `bash scripts/build-release.sh` | `bash scripts/install-release.sh --serial DEVICE` | `artifacts/release/PipBoy-0.3.0-release.apk`, `PipBoy-Compass-0.3.0-release.apk` |
| Debug | `bash scripts/build.sh` | `bash scripts/install-debug.sh --serial DEVICE` | `artifacts/PipBoy-0.3.0-debug.apk`, `PipBoy-Compass-0.3.0-debug.apk` |

Both builds regenerate WFF, run the Python tests, companion unit tests and variant-specific lint. Each output directory has its own `SHA256SUMS`, covering only the current two APKs. Release additionally saves the companion's R8 `mapping.txt` under a versioned name and the public release certificate. Keep the mapping with the matching APK to retrace crashes.

Release disables debugging and enables R8 optimization and resource shrinking for the companion. A narrowly scoped rule suppresses the optional SpotBugs `Nullable` annotation absent from commons-suncalc's runtime dependencies. WFF resources remain unshrunk because the system renderer loads them outside this APK's code graph. Provider/activity names referenced by WFF stay stable. Sensor cadence, publication policy and optional diagnostics are unchanged. Diagnostics recording starts off in both variants. APK size reduction does not establish a battery improvement.

Configure the permanent release key once using [signing and migration](release-signing.md). The build never silently substitutes a debug key or generates a replacement key. The current release has authenticated debug-to-release key rotation. Ordinary unrelated local debug builds cannot update this installation; release-to-debug rollback is refused. Never uninstall as a signature workaround.

After building release, run `bash scripts/test-signing.sh` with both original project 0.2.0 debug reference APKs present in `artifacts/`. It tests both package rotations on API 35 and 36, rejection of the reverse transition, and rejection of an unrelated signer using Android's actual APK verifier. The normal Python suite tests version guards and both-package preflight ordering. Physical configuration retention, providers and active/AOD must also be checked on the watch before calling migration device-verified.

See installation instructions in [English](install.md) and [Ukrainian](install.uk.md).

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
