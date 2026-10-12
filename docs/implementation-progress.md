# Implementation ledger

Historical implementation notes from 2026-10-11. Current behavior and limitations
are documented in [data sources](data-sources.md).

## Baseline and decisions

- Empty source folder, no pre-existing Git repository or application. Initialized
  `feat/pip-boy-wff` in place; no existing branch to isolate or preserve.
- WFF resource-only APK; no phone app and no custom sensor/data provider without approval.
- Reuse workstation Android 36 SDK/JDK and Gradle 8.13 wrapper. WFF 3 / API 35
  is sufficient for the base renderer and works on the Android 17 target.
- Physical device previously verified: SM-L715F, 498x498, density 340, API 37.
- ADB connectivity is intermittent. Explicit connect to the user's current
  endpoint succeeded. Windows adb and its saved pairing keys are used.
- Standard compass app currently advertises only BarometerComplicationProviderService.
  Current Samsung Ultra face is a privileged executable UltraWatchFaceService;
  its compass must not be assumed to be public WFF data.

## Task status

Latest user decision: implement our own public push compass provider and restore
its rotating limb. Version 0.2.0 returns scale 1.0 and slot 3; hour markers stay
fixed. Display/AOD/lock gates stop sensors and all polling while inactive.
Another foreground app can still leave the sensor active on an interactive
unlocked screen; the user accepted that visibility limitation.

Local verification: 15 Python tests, 8 Java tests, both Android lint tasks,
APK builds, official WFF 3 schema and memory checks passed. Read-only review
found service recovery and bottom text orientation issues; corrected to sticky
restart with power gates and counterclockwise bottom text. Both APKs installed successfully. Real push delivery, native sensor unregister
and natural AOD verified; corrected limb and lower readings verified by screenshot; smoothing acceptance pending.

- [x] Install both APKs; select Pip-Boy with DEBUG_SURFACE; verify WFF runtime.
- [x] Build geometry, packaged fonts, measured two-arc calendar and host previews.
- [x] Bind system health/watch battery and installed phone battery provider.
- [x] Implement colored weather and ambient variants, host no-overlap checks.
- [x] Run Python boundary/layout tests, Java heading tests and Android lint.
- [x] Pass official WFF 3 XSD validation and APK memory-footprint validation.
- [x] Observe large time, minute change, health and battery values on physical face.
- [x] Observe native compass heading and sensor stream on physical device.
- [x] Implement replacement public push compass and restore rotating limb.
- [x] Install 0.2.0 and verify live delivery and sleep sensor shutdown.
- [x] Verify corrected limb rendering on active physical face.
- [x] Restore handoff calendar radii, font sizes, START alignment and space-boundary wrapping; host checks pass.
- [x] Observe system calendar event with 20:00 time and long Ukrainian title in two complete arcs on the physical watch; raw TEXT/TITLE fields remain redacted.
- [ ] Physical AOD, all weather temperatures, recovery and 24-hour battery test.
- [ ] Final physical acceptance and source/APK handoff as completed product.

## Physical findings and review

- Both `install -r` operations returned Success, set-watchface returned
  `Favorite Id=[13] Runtime=[2]`; wallpaper service uses Samsung WFF runtime.
- First physical face showed blank text for string concatenation expressions.
  WFF + is numeric only. Replaced those with multi-parameter Template and
  confirmed large 15:50 time plus battery numbers on the physical screen.
- Date Localization on Group did not affect the PartText; moving it localized
  but ICU reordered weekday/day. Explicit weekday/day template now preserves
  English design order. Last date adjustment awaits physical screenshot.
- Native compass screenshot shows N · 002°, sensorservice contains a live
  Rotation Vector stream. This confirms sensor access, not live face updates.
- Permission protection level is signature|privileged|vendorPrivileged;
  pm grant returned `not a changeable permission type`. That old provider returned NoData without the permission; the replacement
  uses public push updates.
- Fresh reviewer found string +, advertised unsupported phone SHORT_TEXT and
  UTF-16 calendar splitting. First two fixed; Unicode wrapping remains an
  explicit unresolved plan requirement. See data-sources.md.
- Physical sleep test did not establish AOD and triggered lock-screen PIN.
  Stopped screen power tests after the user's report. Do not weaken lock settings.

## Verification still requiring physical evidence

Actual calendar event payload, complete active/AOD acceptance, weather recovery,
live compass delivery mechanism, connectivity recovery, and 24-hour battery
observation. Do not mark these complete from host tests or headless editor data.
