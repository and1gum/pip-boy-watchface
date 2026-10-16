# Companion optimization implementation plan

> For agentic workers: use superpowers:executing-plans inline, task by task.

Goal: reduce redundant companion work while preserving current compass motion and wake recovery.
Architecture: bounded optional diagnostics, conservative hot-path changes, then measured conditional provider/scheduler changes.
Tech Stack: Java17, Android35+, AndroidX complications1.2.1, JUnit4.
Spec: docs/companion-optimization-analysis-2026-10-16.md (approved by user's instruction to start).

## Constraints

Keep SENSOR_DELAY_UI,100ms sensor filter,120ms visual motion,33ms cadence,0.03deg threshold,4s heartbeat,5s freshness. Keep display-state subscription,ON/unlocked gate and package exemption. No timer or wake lock added by diagnostics. No normal-use per-sample logging. One runtime toggle,OFF by default. No coordinates in exports. Preserve existing signing/data during device updates.

## Review focus

- Diagnostics OFF allocates no buffer and performs no writes.
- Ring/session bounded; callback success differs from render success.
- Rotation/north crossings and integer labels unchanged.
- AOD/lock/Stop/slot changes still stop sensors.
- Empty/stale/low-accuracy data still hidden; expiry not extended by optimization.

## Tasks

1. [x] Add pure-Java bounded session recorder and tests: OFF no-op,capacity overwrite,counters,timeout,export escaping. Wrap in Android Diagnostics with monotonic time; add runtime toggle and explicit private-file export in CompassActivity. Replace per-push logs with guarded counters/events; record first sample/gates/registration/provider outcomes. No automatic flush timers or location logging. Run failing tests before implementation,then full build.
2. [x] Reuse sensor arrays; consolidate eligibility snapshot within each refresh; cache integer label strings and requester wrapper. Preserve cadence/filter and refresh gates. Add behavior tests where meaningful; compare old/new motion replays including crossings,rotation and stale data. Full build and review.
3. [ ] Fix manual location cancellation ownership and coordinate/cache shared solar results; coalesce pressure only if observations prove overlapping requests. Test cache keys/expiry and independent cancellation. Keep AOD fields and location policies.
4. [ ] Measure diagnostics OFF vs ON and current vs optimized CPU/allocations. Use matched release-equivalent builds. Preserve package/signing and snapshot before install; natural physical wake/AOD check.
5. [ ] Adaptive timer/publication changes only if replay proves same publication decisions AND gate/freshness deadlines remain intact; otherwise record experiment deferred rather than ship a trajectory change. Release/R8 requires final-artifact and signing validation; do not silently replace debug signing.

Checkpoint: checkpoint/pre-optimization-2026-10-16; e6cf68a. APKs preserved in GitHub release.
No energy saving percentage claimed without measurement. Implementation commits remain on codex/companion-optimization until integration.

## Execution evidence

- Tasks1/2: RED recorded by component implementers; full build/lint succeeded with32Java/50Python tests.
- Task3: boundedsolar-daycache and request-specific manualtimeout completed/tested. Networkcoordination/pressurecoalescing deferred until counters demonstrate overlap.
- Final review found preview/live text-cache race; data construction synchronized because preview is Binder-threaded. Host tests cannot execute Android Binder lifecycle; physical preview remains a validation item.
- Task4 pending watch connection/physical checks; no battery/CPU improvement claimed yet.
- Task5 remains conditional; no change shipped to timers,thresholds,cadence,signing or R8.
