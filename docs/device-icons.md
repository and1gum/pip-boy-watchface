# Device icon alignment — 2026-10-11

Latest adjustment: steps scaled uniformly by0.90, watch and phone by0.75
around their own centers. Exact effective sizes are28.8×39.6,22.5×33 and
16.5×33 respectively. The original boxes below remain as authoring bounds;
explicit pivot(0.5,0.5) preserves all three centers and aspect ratios.
The host renderer now also scales Parts around their own pivot.

## Original alignment and source sizes

All three icon boxes have center Y240 (the9–3 axis). Center X is the
vertical projection of each actual sector head, rounded to the nearest
logical pixel because WFF PartImage coordinates are integers:

| Icon | Sector radius / start | Center X | Display size |
| --- | --- | --- | --- |
| Steps |194 /261° |48 |32×44 |
| Watch |166 /100.536° |403 |30×44 |
| Phone |194 /99° |432 |22×44 |

Head Y is approximately270.35 for all three. A9px sector stroke reaches
Y265.85 at its upper cap. Icons end at Y262, giving approximately3.85px
clearance. Height44 is the largest even height that preserves at least3px
clearance and the exact integer Y240 center. The watch/phone boxes leave
3px between them; the steps box begins at X32, clear of the9 o'clock tick
ending near X29. This fixes misalignment caused by start-angle offsets
and transparent padding in square assets.

Assets are authored at their target aspect ratios and saved at2× display
resolution. The watch has a round28×28 face with hands and top/bottom
straps. The phone has a tall20×42 outline with speaker/navigation marks.
Footprints are larger filled shapes. Battery colors tint the complete icon;
all three battery color branches and the unavailable-phone branch share
one positioning helper. AOD visibility and data/provider behavior are unchanged.

Validation:30 Python tests, Android lint/build, official WFF3 schema and
APK memory-footprint checks pass. `artifacts/icons-aligned-preview.png` is
a synthetic host preview; physical screenshots are separate evidence.

Physical validation: final APK installation returned Success.
`artifacts/device-icons-aligned.png` shows the active watchface with the
three enlarged icons centered on the same horizontal axis, directly over
their sector heads. Round watch face and tall phone are visible; the yellow
9/3 marks and the gaps between icons and sectors remain clear.
