# Analog hands — 2026-10-11

## Faceted gold styling — 2026-10-19

Hour and minute hands now use sharp tapered silhouettes, two warm metallic
faces, a narrow directional ridge highlight and a close 25% contact shadow.
The shadow face blends 30% from `#E6AC58` toward `#6D4B27`; the metal body is
opaque. The small 9px dark hub with a 1.3px gold rim sits above the hands.

The supplied screenshot and subsequent Patek Philippe photo are the visual
references. The photo clarifies the broad dauphine silhouette: two longitudinal
facets, a needle tip and a pointed rear end. The adjustable SVG prototype is
unavailable, so the stated 150% width cannot be recovered exactly. Maximum
hour/minute widths are 16.5/13.375 logical pixels, halfway between the earlier
thin 9/6.75px version and the broad 24/20px photo-based version;
lengths remain 147/203px and rear tails 17/22px. Both retain the same 240,240
pivot and time expressions. The seconds subtree, including its open
counterweight, is unchanged.

WFF PartDraw has no arbitrary polygon primitive. `metallic_hand()` in
`scripts/generate.py` therefore bakes polygon geometry into two narrow transparent
PNG assets at 2x logical resolution. Existing WFF groups rotate those images;
there are no new expressions, animations, sensors or runtime filters. The two
uncompressed RGBA images occupy approximately 147 KiB together.

Verification: all 50 Python tests, watchface and companion lint/build checks
passed. A normalized XML comparison confirmed everything outside `hands_layer`
is unchanged and the seconds subtree is identical. Host AOD renders before/after
are pixel-identical. The face APK installed successfully on SM-L715F via ADB;
`artifacts/hands-medium-device.png` is an actual 498x498 watch capture of the
intermediate-width version, with weather and complication values present.
`artifacts/hands-dauphine-device-final.png` records the earlier wide version.
Weather recovery by switching to the adjacent Samsung face and back is
documented in `weather-recovery.md`.
`artifacts/hands-medium-preview.png` is a synthetic preview at 10:09,
not device evidence.
The medium and previous wide APKs are preserved separately as
`artifacts/PipBoy-hands-medium-debug.apk` and `artifacts/PipBoy-hands-wide-debug.apk`.
`artifacts/hands-metal-device-ambient.png` confirms the hands disappear in
natural AOD (device power state `Dozing`). Final code review found no issues.

The earlier revisions below describe the previous appearance.

Compared against prototype-fragment.html pw-hands and DESIGN.md.
The original handoff has rear tails17/22/33px, hour/minute lengths147/203px,
second length190px, an open counterweight at26px behind the pivot and a
dark central hub. The initial WFF omitted the tails and counterweight and
shortened the hour hand to111px.

This revision restores those lengths and tails, with requested heavier widths:
hour6px, minute4px, second2.4px (logical480×480). Amber hands use85% opacity;
seconds remain red. Round caps are retained. The counterweight is a10px transparent
circle with1.8px red outline; its shaft is split around the opening; the hub is9px with2px amber outline. All parts
remain inside the active group and disappear in AOD; time expressions are
unchanged. No additional animation or sensor activity is introduced.

Verification:34 Python tests, Gradle lint/build, WFF3 schema and memory checks
pass. artifacts/hands-preview.png is a synthetic rendering, not device proof.
Device installation returned Success onWATCH_IP:39289. Physical
screenshot artifacts/device-hands.png confirms the heavier hands, rear tails,
red open counterweight and amber-outlined dark hub on the active watchface.

Transparency correction: removed the counterweight Fill and split its shaft
at Y260.5/271.5 so neither the shaft nor a background disk covers the interior.
Build,34 Python tests and WFF3 validation passed.

## Hand stacking — 2026-10-12

The steps group was lifted to a later Scene position for tap handling and could
cover the hands. The active hands now form the final Scene group. The group is
hidden in ambient mode; within it the hour hand is drawn first, then minute,
then second. Every complication, step sector and other readout is below them.
The center pin is drawn below the hands. Host ordering test and full build/lint
passed. On the Galaxy Watch Ultra2, the updated APK installed successfully and
its steps icon still opened Samsung Health Steps. A direct watch screenshot with
the second hand on the left is in `docs/images/hand-order-on-watch.png`. Weather
was temporarily unavailable after reinstalling, as described in
`docs/weather-recovery.md`; the screenshot is unedited.
