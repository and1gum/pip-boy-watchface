# Optional companion diagnostics

[Українською](companion-diagnostics.uk.md) · [Troubleshooting](troubleshooting.md)

Diagnostics are OFF on installation/process restart. Open Pip-Boy Compass and
press **Start diagnostics**, return to the face and reproduce the issue. Collection
uses a bounded memory ring (1,024 events), aggregate counters and a 15-minute
limit checked when the app next executes. It adds no timers, sensors or wake locks.
**Stop diagnostics** retains the bounded snapshot for export. Starting again
replaces it. A killed process loses its in-memory recording; it is not crash storage.

Press **Export diagnostics** to write `files/diagnostics.json` in private app data.
For the currently signed debug build, retrieve it with the current ADB endpoint:

```sh
adb -s WATCH_IP:CONNECT_PORT shell run-as ua.and1gum.pipboy.compass cat files/diagnostics.json > diagnostics.json
```

The file contains event names, monotonic timestamps, UTC anchor, app/process/SDK
metadata and counters. It does not contain coordinates, calendar entries or a
system-wide log. Sensor reported power is metadata, not measured app energy.
The initial gate mask uses enabled=1, bound slots=2, display ON=4, unlocked=8.
A mask of 15 permits tracking. `dataAccepted` means the provider callback returned
normally; it does not establish visible watch-face rendering. `providerDisconnected`
is a separate failure event. A gap cannot itself establish Samsung freezing; use
external system logs to investigate that.

Normal use requires no recording or export. OFF performs no diagnostic clock
reads/writes and allocates no new session buffer. After Stop or timeout the already
recorded bounded buffer remains for export until a new session or process restart.
For battery comparisons leave diagnostics OFF and disconnect ADB/debugger/live
logcat; match AOD, brightness, connectivity and exemption settings between runs.
