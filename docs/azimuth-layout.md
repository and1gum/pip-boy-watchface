# Fixed azimuth readout — 2026-10-11

The readout now uses the date's embedded Liberation Mono Bold font and
shared size 25. It remains curved, centered on the bottom (180 degrees),
with counterclockwise text on radius 226 so it reads upright.

The provider publishes eight cardinal directions and zero-padded magnetic
degrees from 000 to 359 (`Heading.label`). All 360 labels are measured using
the packaged font. Maximum width is 135 logical pixels (nine characters),
for example `NE · 023°`; all diagonal directions have the same maximum.

At radius 226, text occupies 34.225 degrees. Six pixels of clearance per
side require 37.268 degrees; the fixed gap is rounded up to 38 degrees,
from 161 to 199. Text follows the reverse arc, 199 to 161.

The background mask has radius 221 and stroke thickness 32: it covers
radii 205 through 237, including the fixed hour marks (211–218), rotating
compass ring (218), outer ticks (up to 232) and bottom cardinal letters.
BUTT end caps preserve the calculated angular gap instead of widening it
with rounded stroke caps. Hour marks inside the same angular interval are
omitted explicitly. EMPTY data uses the same font, arc and gap with `—`.

No provider/sensor changes. The gap/readout disappear in AOD with the
compass slot. Tests cover date-font equality, all possible label widths,
shared live/EMPTY geometry and mask coverage of both scales.

Validation: 27 Python tests, Android lint/build, official WFF3 schema and
APK memory-footprint checks passed. APK installation returned Success.
`artifacts/device-azimuth-25.png` is a physical active screenshot showing
`N · 351°` at the larger curved size, with the tight bottom gap and no
visible tick behind the label. Maximum-width diagonal labels were measured
and covered by tests; this capture itself shows a shorter cardinal label.
