# Pip-Boy Compass 0.2.0

Watch-only implementation using Android SensorManager and public complication
update requests. No proprietary source copied, GPS, phone application, privileged
permission, or wake lock. Magnetic heading is relative to the upper screen edge;
it is not corrected to true north.

## Lifetime and power

A specialUse foreground service keeps the sensor client eligible while the face
is active. Tracking requires an enabled provider, at least one bound instance,
PowerManager interactive state, Display.STATE_ON, and unlocked keyguard.
Display and screen events recheck these gates. On inactivity the service removes
the sensor listener and all timer callbacks, clears readings, and requests NoData.
The idle service remains for wake events. START_STICKY requests process recovery;
Android can delay restart. A boot/package-update receiver restarts the service
when the compass is enabled and a slot remains assigned. Force-stop requires
reopening the application.

The public API does not expose exact watchface visibility. Tracking may continue
inside another app while the screen stays interactive and unlocked. Removing the
last instance or pressing Stop ends the service. No claim of zero battery use is
made; a physical overnight/day measurement remains required.

## Data and rate

Rotation-vector sensor at SENSOR_DELAY_UI, existing accelerometer/magnetometer
fallback. The current experimental source interpolates continuous headings with
a 120 ms time constant on a separate 33 ms software timer. Sensor sampling stays
at SENSOR_DELAY_UI. Changed values publish at most about 30 times a second;
stationary heartbeat every four seconds. This is not yet a verified production
smoothness or battery improvement. Values require accuracy >= LOW and measurement age <5 seconds;
complication validity is five seconds. Invalid data produces NoData, never a
fake north. The WFF slot rotates the limb by minus the numeric heading, preserves
fixed hour marks, and hides the compass in ambient mode.

The runtime may throttle public push delivery. This is not a promise of Samsung
stock-compass smoothness. Physical rate, expiry handling, and wake recovery must
be established on the target watch.

## Verification

15 Python layout/data tests and 8 Java heading/policy tests passed, both APKs
built with lint; official WFF 3 schema and APK memory checks passed. Reviewer
findings about process recovery and bottom heading orientation were corrected.
Host previews use synthetic values; they do not prove physical delivery.

## Physical evidence, 2026-10-11

Both install -r commands returned Success; DEBUG_SURFACE selected Pip-Boy.
Initial automatic foreground-service startup was denied by Android. Opening
CompassActivity once successfully started the foreground service. Subsequent
public requests delivered changing values at roughly 1 Hz (357, 4, 7, 350 etc.).
The face screenshot showed a real numeric NE 031° reading.

An initial small heading-label bound cropped the restored rotor on the device.
A full-circle BoundingArc still clipped content on the target renderer. Final
implementation uses a full-face BoundingOval; the compass is before the
narrower calendar and phone slots to preserve their tap targets. Phone bounds
also cover its bottom percentage. Cardinals follow original upright N/E/S/W
positions, north amber, with counterrotation inside the rotating limb. Build,
lint, tests, official schema and memory checks passed again, APK installed.
[WFF bounds crop rendering](https://developer.android.com/reference/wear-os/wff/complication/bounding).

Logs at16:51:46 and16:52:18 report sensor stop and delivered NoData, followed
by start and renewed readings on natural wake. Sensorservice history confirms
actual Rotation Vector unregister at16:51:46; WakeLockRefCount0 while active.
A natural AOD screenshot shows only time/date/weather/quiet rim.
Active screenshot confirmed full limb/cardinals and lower readings. A later
provider-binding check showed that the initial phone 48% matched compass48°: it
was not valid battery evidence. Restored original slot declaration order; runtime
now confirms phone dataSource=com.weartools.phonebattcomp and compass
dataSource=ua.and1gum.pipboy.compass. Preserve slot order across updates.
No screen power keys or PIN settings changed. Long-term battery use, process-kill
recovery and sustained delivery rate remain unmeasured.

## Smoothing update

Sensor readings use a circular exponential filter (100ms time constant); elapsed
sensor time controls the filter. Continuous degrees across north avoid full-turn
359→0 animation. RANGED_VALUE carries these continuous degrees with encompassing
min/max, while SHORT_TEXT and heading labels stay normalized0–359. WFF rotation
and cardinal counterrotation animate linearly over0.16s at60fps. Only active
changes request updates at most8Hz; sleep has no animation or polling. The initial 4Hz build
delivered updates about0.25–0.3s apart; increased to8Hz at user request.
Subjective smoothness still
requires user acceptance; no claim of stock Samsung equivalence.

Display rotation is refreshed before sensor remapping, fixing stale wrist/display
orientation without restarting the service. Two added Java tests cover both
north crossings, jitter filtering, convergence and reset. Final count8Java/15Python.

A later physical screenshot showed phone97%, watch68% and compassN001°,
confirming independent bottom readings. Near-full phone sector at97–98% is
expected. Full-face compass bounds may capture taps; numeric data independence
is verified but complete editor/tap interaction acceptance remains pending.

Final8Hz device logs show changed-heading deliveries about0.13–0.2s apart.
User confirmed phone97% visible. Battery labels shifted6° toward sector ends
(center169.5° instead of175.5°) to match original handoff positions.

Label placement APK passed build/lint/tests, WFF schema and memory validation;
installation returned Success after reconnect to the unchanged endpoint46163.

## Further smoothness investigation

User requested substantially smoother visual interpolation without higher sensor
sampling and no compass tap action. Removed provider tapAction from both payload
types; installed. Captured15s screen recordings: baseline112frames (median132ms),
without outer Condition105frames (median139ms). Condition-reset hypothesis was
not supported; these frame counts do not prove the panel cannot render faster.
System animator scale1.0 and display60Hz confirmed. The clock-driven transform
experiment produced108frames (median144ms), also without the desired improvement.
Clock nudging and Transform/Animation have been removed from the experimental
release source. Sensor/push interpolation is now implemented and passes host
tests, but physical smoothness remains unverified. Display-orientation changes
reset both continuous sensor and visual filters, preventing accumulated-angle
spins. Slot preferences are written only when membership changes. Payloads have
no tapAction; tapping the limb does not intentionally open the provider.

See [Samsung/WFF animation research](samsung-animation-research.md) for the next
controlled test, which separates angular-animation settings from complication
delivery. Final source build passed15Python tests,10Java tests and both Android
lint/assemble tasks; this does not establish physical rendering success.
