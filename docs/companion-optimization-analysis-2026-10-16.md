# Companion optimization analysis — 2026-10-16

Read-only code and dependency audit using Superpowers brainstorming and parallel
analysis of compass, environment providers, and diagnostics. This is a proposal,
not an implementation specification. No app code, APK, sensor settings, or watch
configuration was changed. Current accepted compass smoothness and wrist-raise
recovery are requirements. Energy savings have not been measured.

## Current workload and what it means

| Path | Current behavior | Evidence |
| --- | --- | --- |
| Sensor | Rotation vector, `SENSOR_DELAY_UI`; event-driven callbacks, not an 8 Hz polling loop | `CompassSensor.java:25-29,37-40` |
| Motion | 100 ms sensor smoothing plus 120 ms visual motion; a 33 ms timer while eligible | `SmoothedHeading.java:10-15`, `HeadingMotion.java:12-17`, `CompassTrackingService.java:37-43` |
| Publication | Changed continuous value at >=0.03 degrees and >=33 ms; stationary heartbeat at 4 s | `TrackingPolicy.java:10-11` |
| Freshness | Measurement age <5 s, accuracy >=LOW; payload valid for 5 s from creation | `TrackingPolicy.java:13-14`, `CompassSource.java:42` |
| AOD | Compass unregisters sensor and stops motion timer; eligibility retry uses Handler every 10 s | `CompassTrackingService.java:120-123,141-150` |
| Pressure | Independent 1.5 s burst per request; nominal requested update interval 300 s | `PressureSource.java:22-53`, `AndroidManifest.xml:46` |
| Solar | Nominal hourly requests; two slots; approximate network acquisition throttled by 30-minute attempt guard | `SolarSource.java:46-73`, `AndroidManifest.xml:61`, `scripts/generate.py:663-669` |
| Distribution | Existing build script produces debug APKs | `scripts/build.sh:9-12`, `compass/build.gradle.kts:2-17` |

Java paths in this report are under `compass/src/main/java/ua/and1gum/pipboy/compass/`.
A 33 ms publication opportunity is not 30 visible frames/s or 30 sensor samples/s.
The current WFF rotates directly from the continuous ranged value, with no compass
Animation element (`scripts/generate.py:583-592`). Cutting publication frequency
can change the accepted motion.

The exact AndroidX 1.2.1 AAR from the local Gradle cache was inspected with `javap`.
`ComplicationDataSourceUpdateRequesterImpl.requestUpdateAll()` constructs an Intent,
obtains a PendingIntent, then sends a broadcast on every call. The app creates its
component/requester wrapper each time too (`CompassSource.java:16-18`). This is a
cross-process update pipeline, not a cheap in-process repaint. Caching the wrapper
alone does not remove those PendingIntent/broadcast operations. Actual system cost
requires profiling; there is no measured battery attribution yet.

## First candidates: preserve cadence and output

| Priority | Concrete change | Expected work reduction | Risk and validation |
| --- | --- | --- | --- |
| 1 | Optional diagnostics, OFF by default; gate before formatting | Remove per-push/per-response diagnostic strings/logging in normal use | Compare recorder OFF/ON overhead; retain meaningful errors |
| 1 | Reuse sensor matrix/remap/orientation arrays | Three fewer array allocations per sensor event (`CompassSensor.java:55-64`) | Same math/order; replay headings and rotation changes |
| 1 | One consistent eligibility snapshot per refresh | Avoid duplicate display and preference lookups (`CompassTrackingService.java:92-107,120-123`) | Keep gate checking cadence initially; test all pause/resume gates |
| 2 | Cache immutable text for repeated integer headings | Avoid repeated formatting while continuous subdegree output changes (`CompassSource.java:40-45`, `Heading.java:12-14`) | Preserve continuous float, accessibility text, and new validity range |
| 2 | Reuse requester/component with suitable context lifetime | Remove wrapper allocations per push (`CompassSource.java:16-18`) | Small benefit; does not remove broadcasts; avoid retaining Activity |
| 2 | Prepare and test a release build with R8 | Remove debug deployment overhead and optimize unused/reachable code | No promised energy percentage; test entry points/library keep rules and signing/update path |

The active 33 ms refresh presently obtains the display twice, reads enabled/slots
more than once, queries keyguard and removes the paused retry. These API call
counts are code facts; not every call necessarily makes a Binder transaction or
reads a file. SharedPreferences reads normally use in-memory data.

First consolidate repeated work within one invocation. Moving every gate check
out of the animation tick immediately is riskier: earlier device evidence showed
missing unlock events. Preserve explicit display-state subscription, ON/unlocked
checks and a fallback eligibility path while measuring candidate changes.

## Larger opportunities: measure and isolate

### Stop unnecessary motion work when it has settled

The motion timer continues every 33 ms while eligible, including after the
published float no longer changes. Sensor callbacks also advance motion and
invoke publication, so some samples have zero elapsed time. An elapsed-zero fast
path can avoid redundant exponential calculations. Adaptive timer scheduling
could do more, but must retain:

- the existing trajectory while moving and immediate first valid fix;
- a 4 s heartbeat even while stationary;
- NoData at measurement freshness expiry, including a stalled sensor;
- immediate resume when a new target arrives;
- display, lock, Stop and slot-removal handling.

One or several identical published floats do not prove convergence: the internal
double can still cross a future float boundary. Require exact settled-state
detection or proof that skipped publications are unchanged, with slow-approach
and rounding-boundary replay cases. Preserve the current bounded fallback gate
check initially: replacing its approximately 33 ms opportunity with a 4 s
heartbeat would worsen detection of a missed lock/display event. Any relaxation
of that bound needs separate lifecycle acceptance and device testing.

Exact convergence/float saturation is different from introducing an arbitrary
"stationary" epsilon. An epsilon can change output and suppress tiny real motion.
Sensor jitter may keep the timer active anyway. Removing the timer does not itself
stop the rotation-vector sensor. Replay output and publication decisions before
claiming this preserves smoothness.

### Avoid redundant system update requests

The existing 33 ms publication guard already suppresses many sensor/timer calls.
There is no evidence that both callers cause two broadcasts inside that interval.
Measure requested updates, incoming provider requests, response latency and visible
latency separately before adding coalescing. Any coalescing must let first-fix,
pause/NoData and freshness-expiry updates bypass delays. Reducing publication to
8 Hz, rounding to whole degrees, or replacing the continuous value with modulo
360 is a separate visual experiment, not a safe default optimization.

The 0.03-degree threshold spans about 0.11–0.12 authored pixels at the compass
radii. This makes a threshold experiment plausible, but does not establish that a
larger threshold is invisible on the real display.

### Share solar work across the two slots

Both sunrise and sunset slots use one provider and each request computes both
times (`scripts/generate.py:663-669`, `SolarSource.java:47,78`). A fresh location
also causes a refresh-all after the requesting slot was already delivered
(`SolarSource.java:65-67`). Cache the computed day result by local date, time zone
and location; preserve sibling-slot refresh, date/time-zone invalidation and the
current location freshness policy. This reduces duplicated CPU/provider work;
its actual frequency and energy contribution are unknown.

The manual location Activity independently requests network location, immediately
refreshes the provider, then refreshes it again on completion
(`EnvironmentActivity.java:23-29`). The Activity does not coordinate its request
with the provider's attempt guard. A shared in-flight acquisition can prevent
concurrent network requests without postponing the cached display.

There is also a correctness bug: an older 20 s timeout reads the mutable `cancel`
field and can cancel a newer request (`EnvironmentActivity.java:25-27`). Capture
the request's cancellation signal and remove its timeout on completion/destruction.
This belongs in a focused reliability fix, not a battery-saving claim.

### Share overlapping pressure bursts only if they occur

Each pressure request independently registers and samples for 1.5 s
(`PressureSource.java:22-53`). A single in-flight burst can satisfy concurrent
requests. Normal configuration has one pressure slot, so verify overlap first.
Blind caching across non-overlapping requests changes freshness.

At the nominal 5-minute interval this is 18 seconds of requested sensor sampling
per hour, not a measured energy cost. Four-hour history admits at most about 49
regular samples (`PressureHistory.java:27,33`). History decoding and sorting a
small burst are lower priorities. Pressure and solar are intentionally visible
in AOD; disabling them there is a feature change.

## Proposed diagnostic mode

Recommend one user-controlled diagnostic session in the same companion, OFF by
default. Normal use should run a release build. A runtime OFF check has a tiny
branch cost; do not call it mathematically zero overhead. Do not maintain two
simultaneously installed provider apps or automatically start diagnostics on boot.

When OFF: no collector buffers, extra timers, listeners, wake locks, file writes,
exports, or hot-path diagnostic formatting. Preserve ordinary error handling.
When ON:

- Allocate a bounded ring, e.g. 1,024 compact records, for lifecycle and gate
  transitions, callback origin, registration, first sample, accuracy, stale data
  and provider failures. Record overwritten count.
- Keep aggregate counters/histograms for samples, validity/accuracy, registration
  duration, ticks/lateness, publish decisions, update requests, provider responses,
  NoData and errors. Do not write a JSON/text row for every 30 Hz update.
- Timestamp events monotonically, with one wall-clock anchor and process/build ID.
  Record requested and actual sample intervals separately.
- Bound the session and export JSON/CSV manually, outside the sampling path.
  Any timeout implementation must not create a new periodic wake mechanism.
- Exclude coordinates, calendar data and unrelated logs by default. Keep files
  private and make export explicit. Crash-survival checkpoints add I/O and require
  a separately measured policy; do not pretend an in-memory ring survives death.

Correct the existing `Delivered` log: it currently executes even after a caught
RemoteException (`CompassSource.java:34-36`). Record payload kind/age and whether
the callback returned normally. A normal callback return is not proof the face
rendered it. The provider supplies data; WFF controls rendering.

A frozen process cannot log while frozen. A silent interval alone cannot prove
Freecess: correlate it with external OS logs. Do not add a wake lock or continuous
polling to hide this distinction. Keep the verified package exemption and explicit
state subscription as fixed conditions during optimization comparisons.

## Measurement and acceptance

1. Replay old/new motion using the same headings and timestamps: jitter, constant
   target, quick reversal, repeated north crossings, continuous turns, irregular
   delivery, rotation reset, low accuracy and a >=5 s gap. Compare floats, labels
   and publish/no-publish decisions, not merely final direction.
2. Profile short matched sessions for allocations, CPU time and cross-process
   work. Measure collector OFF versus ON first; then one optimization at a time.
3. Use normal release-equivalent builds for battery comparisons, with diagnostics
   OFF, ADB/debugger/live logcat disconnected, and the companion Activity closed.
   Keep firmware, whitelist, radios, brightness, AOD, movement and thermal state
   comparable. Prefer repeated ABBA runs to one short percentage reading.
4. Separately verify natural raises after longer AOD waits, lock/unlock, Stop,
   slot changes, process restart and missing/stalled samples. Check actual visible
   recovery and sensor shutdown, not just successful installation.
5. Record battery/charge-counter deltas if supported and whole-device workload;
   battery percentage over a short run is too coarse. Do not reset batterystats
   or change global freezer/idle settings for this comparison.

Android Power Profiler's ODPM support cannot be assumed on this Samsung watch;
reported Sensor.getPower is metadata, not measured app energy. Sensor-duration
estimates omit CPU, broadcasts, rendering, radios and shared hardware.

Recommended order: diagnostics and baseline; low-risk allocation/snapshot/text
changes at unchanged cadence; solar/pressure duplication if observed; adaptive
stationary timer only with replay and device evidence. Publication/sensor rate
experiments come last and require fresh visual acceptance.

## Sources and limits

- [Complication update requester contract](https://developer.android.com/reference/androidx/wear/watchface/complications/datasource/ComplicationDataSourceUpdateRequester): request-all updates every active instance of this provider; not every watch complication.
- [Complication responsibilities](https://developer.android.com/training/wearables/complications): provider data versus watch-face rendering.
- [Sensor best practices](https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview): unregister when data is not needed.
- [R8 release optimization](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization): configure and test the actual release artifact.
- [Power Profiler support and measurement limits](https://developer.android.com/studio/profile/power-profiler): device support, device-level readings and noise.

No new benchmark, battery run, sensor-rate experiment or visual comparison was
performed for this analysis. Earlier freezer/exemption trials are documented
separately in `compass-resume-diagnosis-2026-10-16.md` and do not measure energy.
