# Analog hands — 2026-10-11

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
