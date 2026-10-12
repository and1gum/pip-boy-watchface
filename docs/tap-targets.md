# Tap targets — 2026-10-11

Requested destinations:

| Visible target | Destination |
| --- | --- |
| Weather NOW / +3 / +6 labels | Existing Samsung Weather launch |
| Calendar text arc | Existing NEXT_EVENT complication PendingIntent; no rectangular upper-screen target |
| Azimuth readout | Samsung Compass MainActivity |
| Steps icon and full sector | Samsung Health StepsActivity |
| Watch and phone battery icons and full sectors | WFF BATTERY_STATUS system screen |
| Steps count, watch percentage, phone percentage | Samsung Compass MainActivity |
| Pulse reading (heart icon is decorative) | WFF HEALTH_HEART_RATE → Samsung Health HeartRateActivity |

Compass and steps activities were successfully launched explicitly through
ADB on the target watch. Local Launch elements are attached to the visible
icons and readouts. Circular text uses local Part bounds and an offset circle
center to preserve its absolute geometry. Full-face parts carry no Launch.
The compass complication now uses outer-ring rendering bounds, and slot
order remains calendar, phone battery, compass to preserve Samsung bindings.
Sector strokes now carry local tap actions (see the October 12 update below).

Validation: 34 Python tests pass, Android lint/build succeeds, official WFF3
schema validation and APK memory-footprint checks pass.

Physical verification used ADB-generated taps on the active watchface at
498×498. Native destinations were confirmed from topResumedActivity:
Compass MainActivity, Samsung Health StepsActivity, Samsung battery settings
BatteryMainActivity, Samsung Weather WeatherActivity and Calendar DetailActivity.
Initial watch-icon taps were intercepted by the overlapping phone complication.
The watch icon is now raised into a scene-level group above the slots, retaining
its color conditions and AOD hiding. Slot declaration order is unchanged.

Final APK installation returned Success onWATCH_IP:39289. All nine
tap checks passed after allowing the native screens two seconds to resume.
Recorded evidence: artifacts/device-tap-verification.txt.

## Calendar touch correction — 2026-10-12

The calendar's former `(50,22,380,160)` rectangle intercepted taps on the
main time and on Samsung's top mode indicator. A physical tap at `(249,165)`
opened Calendar DetailActivity before the change.

Use a `BoundingArc` centered at `(240,240)`, outer radius 196, thickness 50,
angles -60 to 60. Calendar text radii are now 180 and 159 with the same 20px
font. This keeps the mode indicator center `(249,38)` on the 498px device
outside the calendar target. The calendar text itself remains tappable.
WFF shares its rendering clip and interaction bounds, so zero-sized bounds
also hide the event; this approach was rejected after physical verification.
Reference: [WFF bounding areas](https://developer.android.com/reference/wear-os/wff/complication/bounding).

The preceding arc at outer radius 214 freed the main time but still captured
the mode-indicator tap. The final radius-196 revision is installed. The compass
also uses a `BoundingArc` with outer radius 240, thickness 32 and angles 0 to
359.99, leaving the center free. Samsung treats an exact 0-to-360 arc as empty;
the 359.99 revision visibly preserves the rotating limb and azimuth.

Validation: 36 Python tests and Android lint/build pass; installation returned
Success on `WATCH_IP:44463`. The final physical screenshot preserves the
event, limb and azimuth. Tapping the main time stays on SysUiActivity rather
than opening Calendar DetailActivity. Evidence:
`artifacts/calendar-final-touch-verification.txt`, `artifacts/sleep-off-confirm.png`.

Mode-indicator behavior is NOT fixed or claimed working. Both ADB and the
user's physical touch on the Sleep icon did nothing on Pip-Boy. For comparison,
temporarily switched to Samsung Simple Digital: the user's physical touch did
nothing there either. Restored the existing Pip-Boy favorite (13), turned off
the temporary Sleep mode through Quick Panel > Modes > Sleep, and confirmed
zen_mode=0. The calendar text arc itself remains tappable; WFF exposes no
separate switch to remove the system provider's PendingIntent while keeping
its rendered data.

## Steps and battery interaction — 2026-10-12

Icons and complete sectors open their native steps/battery destination.
All three numeric readouts, including missing-data dashes, open Samsung
Compass so it remains reachable while Now Bar covers the bottom azimuth.

Visible sectors consist of small `PartDraw` arc segments with local `Launch`
elements. Their bounds follow the arc rather than covering the rectangular
interior of the sector. Background segments remain interactive at any progress;
filled segments preserve the same destination. Numeric bounds are tightened
around the glyphs to avoid intercepting taps at sector endpoints.

The watch sector, icon and percentage are raised above the phone complication
with their battery-color conditions intact; the steps group is also above it.
The phone's own sector and numbers stay in its complication scope.
All raised groups retain their ambient hiding.

Reference: [WFF PartDraw and Launch](https://developer.android.com/reference/wear-os/wff/group/part/draw/part-draw).
Host verification: 38 Python tests and Android lint/build pass. Installation
returned Success on `WATCH_IP:44463`. Physical tests confirmed all nine
icon/sector/number destinations, plus all three sector endpoints (including
the unfilled watch-battery tail). The final three numeric taps opened Samsung
Compass, icon/sector taps opened StepsActivity or BatteryMainActivity.
Initial probes outside the icons and one short activity-transition wait were
repeated using the icon centers and a two-second wait; all retries passed.
Evidence: `artifacts/sector-taps-device-verification.txt`,
`artifacts/sectors-installed.png`. Returned to Pip-Boy after testing.

## Heart rate shortcut — 2026-10-12

The outlined heart, all five colored heart states, the pulse reading and its
missing-data dash use `Launch target="HEALTH_HEART_RATE"`. The visible heart
group is above the phone complication so its overlapping bounds cannot steal
the tap; ambient hiding is preserved. No permissions or provider changes.

39 Python tests and Android lint/build pass. Installation returned Success.
Physical taps on the heart and the number both opened the installed Samsung
Health `com.samsung.android.wear.shealth/.app.heartrate.view.HeartRateActivity`.
Initial probes during reload/an incoming notification were retried after
returning to the face. Evidence: `artifacts/heart-tap-device-verification.txt`,
`artifacts/heart-rate-native.png`. Returned to Pip-Boy after testing.

## Shared weather target — 2026-10-12

One rectangle at logical (80,242), size 295×78, opens Samsung Weather.
It sits below the clock, above the heart, between the steps and battery sectors.
A nearly invisible black fill (#01000000) retains hit testing; the target is
above all complication slots and hides in ambient mode. Weather labels no
longer have separate launch targets.

40 Python tests and Android lint/build pass. Installation returned Success.
Device taps at all four rectangle corners and its center opened WeatherActivity.
Neighboring sectors opened StepsActivity and BatteryMainActivity; pulse opened
HeartRateActivity; tapping the clock stayed on the watch face. Evidence:
`artifacts/weather-taps-device-verification.txt`.

## Health and solar panel — 2026-10-12

Pulse uses a 48 px font; heart and number open HEALTH_HEART_RATE.
Both number edges were verified on the watch. Pressure and solar slots append
IDs 4, 5 and 6, preserving earlier bindings. Solar hit boxes remain outside
the main time, and both text and icons open the companion's solar details.
The shared weather rectangle retains priority; both edges opened WeatherActivity.
Unknown pressure trend has a neutral column. The pressure column now spans
y=332…385 with no direction symbols; its color indicates the trend, while
the pressure number remains beside it.

## Continuous sector strokes — 2026-10-12

Steps and battery progress strokes now use one continuous Arc per track/fill.
The previous 5-degree visible pieces produced antialiasing seams. Small local
Rectangle surfaces with alpha 1 retain touch coverage over the entire sector,
including its unfilled portion. The visual arcs have no Launch; step targets
still open StepsActivity and battery targets still open BATTERY_STATUS.


Latest touch refinement: the heart icon has no Launch; only the pulse number
opens HEALTH_HEART_RATE. Samsung Health can restore its last activity when
StepsActivity is launched directly with NEW_TASK. StepsLaunchActivity forwards
with NEW_TASK | CLEAR_TOP so the step icon/sector reliably opens StepsActivity
after the user has viewed heart rate. The pressure font is 25 px, matching date
and azimuth, with its left anchor unchanged.

Physical final verification: step-sector tap after heart rate and the step icon
both opened StepsActivity; pulse digits opened HeartRateActivity before and
after steps; tapping the decorative heart stayed on SysUiActivity/watch face.
Both battery sector destinations were verified separately. The final screenshot
shows continuous arcs, 25 px pressure digits and restored weather. Evidence is
local in artifacts/continuous-sector-final-taps.txt and artifacts/sectors-final.png.
Validation: 46 Python tests, companion unit tests and both Android lint/builds pass.

Weather balance refinement: shift all three weather columns 12 logical pixels
left, including labels, temperatures, icons, missing/error states. Weather hit
rectangle is now (70,242,305,78), retaining its former right edge and clearing
the step and battery strokes. No per-icon targets are introduced.

Approved upper layout: calendar text and its BoundingArc span -50° to +50°.
Outer calendar and both solar time labels share radius 194; inner calendar stays
at 173. Solar centers move to ±67.5° (26° text containers), with horizon icons
at y=160. The solar complication bounds remain local and cover the raised labels
and icons. Weather, pulse and sector targets retain their prior geometry.

Solar icon refinement: each 33px icon center lies on the radial ray through its
time's colon (±67.5°). The visible icon-to-time gap matches the time-to-surrounding
compass circle gap (radius 218), measured with the font and icon alpha mask.
Sunset bounds extend to x=380 with width 82 to contain its moved icon. Pressure
unit label moves up from y=365 to y=362; pressure and other touch targets stay as-is.
