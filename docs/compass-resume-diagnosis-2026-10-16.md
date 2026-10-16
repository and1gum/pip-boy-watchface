# Compass wrist-raise failure: Samsung Freecess

The reported three consecutive failures were captured on SM-L715F with the
updated compass companion. No additional runtime changes were made during this
investigation. The immediate blocker is Samsung freezing the companion process
while its foreground service remains registered.

## Evidence

The selected device log is saved locally at
`artifacts/diagnostics/2026-10-16-compass-resume/freezer-timeline.log`.
Times below use the device's local clock.

| Event | Evidence |
| --- | --- |
| 10:31:27.970: companion PID 16442 frozen | Log line 1: `MARsmini_FreecessController$LcdOffFreezer`, `FZ`, reason `LEV` |
| Three wrist-raises at 10:32:01.806, 10:32:09.526, 10:32:18.434 | Log lines 2–4: display ON, reason TILT; retained application log contains no sensor start in these intervals |
| 10:33:58.182: same PID unfrozen | Log line 5: `UFZ`, reason `screenOn-widget` |
| 19 ms later: sensor starts | Log line 6: `Sensor started=true displayState=2 interactive=true` |
| 240 ms after unfreeze: heading delivered | Log line 7: `Delivered 57` |

The live service dump still showed PID 16442 and `isForeground=true`, without
a process restart. Battery Saver was OFF. An OFF Battery Saver state therefore
did not rule out Samsung's separate process-freezing mechanism.

## What the previous checks missed

Two successful wrist-raises shortly after installation tested recovery while
the process was runnable. They did not test recovery after Freecess froze it.
The display policy and explicit state subscription can handle a running process;
neither can execute Java callbacks or Handler retries inside a frozen process.
Host policy tests also do not exercise the vendor freezer.

The previous reliability conclusion was too broad. Keep the changes' measured
benefit separate from the unresolved freezing problem.

## Limits and next controlled test

The logs establish freezing as the immediate blocker for these three failures.
They do not establish why Samsung freezes this foreground service or whether a
per-app battery optimization exemption prevents it. That requires a controlled
test, not another timer change.

Record the current per-app optimization state, observe a baseline freeze, then
test one supported package-specific exemption with the same natural
AOD → wrist-raise lifecycle. Avoid opening the companion or touching the screen
during trials; full wake can unfreeze the process and conceal the failure.
Require successful heading delivery after longer AOD intervals as well as quick
repeated raises, and verify sensors stop again in AOD. Restore the setting if
the exemption has no effect. Do not disable the freezer globally.

Analysis followed Superpowers systematic-debugging and a separate read-only
review of lifecycle and timer hypotheses. No new APK or battery setting was
changed in this investigation.

## Package-specific exemption trial

In the subsequent user-authorized trial, the companion was absent from the
initial device-idle whitelist (saved as `whitelist-before.txt` beside the local
timeline). At 10:40:21, only this package was added:

```sh
adb shell cmd deviceidle whitelist +ua.and1gum.pipboy.compass
```

The command returned `Added`, and reading the list back confirmed
`user,ua.and1gum.pipboy.compass,10215`. No APK, service implementation, global
freezer setting, or other package exemption was changed.

The sensor stopped at 10:40:46.244. Following 78.5 seconds of AOD, three natural
wrist-raises delivered the first heading after 0.460, 0.469 and 0.467 seconds.
Each return to AOD stopped the sensor and delivered NoData. No FZ for the
companion appeared during the retained trial. The user confirmed physical
visibility in all three attempts. Final dumps showed Dozing, no active compass
sensor connection, and the exemption still present. Evidence:
`artifacts/diagnostics/2026-10-16-compass-resume/whitelist-trial-timeline.log`.

The exemption remains enabled for this companion. Restore the recorded initial
state with:

```sh
adb shell cmd deviceidle whitelist -ua.and1gum.pipboy.compass
```

This is a successful controlled trial of three raises, including one longer
ambient interval. It does not establish overnight battery cost or reboot/update
behavior. Battery-use measurement remains outstanding.
