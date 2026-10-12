# Watchface design specification

## Goal and visual hierarchy

Round hybrid watchface in Fallout Pip-Boy terminal style for the user's Samsung Watch Ultra device. The exact device model and OS version need verification in the implementation environment.

Digital time is the primary readable information. Thin analog hands remain as a decorative and secondary time reference. Show date, upcoming calendar event, three weather samples, pulse, steps, both device batteries, and compass in active mode. Information inside the product face uses English; sample prototype controls outside the face are Ukrainian.

## Accepted decisions

- Black background, green terminal typography, amber analog hands and hour markers, bright red second hand.
- Main time and calendar event start time use 24-hour format. Weather timestamps now also use 24-hour format: NOW / 13:00 / 16:00. Those forecast times are sample data, not fixed production hours.
- Date includes weekday and day number, without month. Sample `SUN 11`.
- Main time is above the hand pivot, centered vertically in the space between the bottom of the date and the hand pivot. No brackets around the time.
- Calendar text follows two concentric arcs within the upper sector from 10 o'clock to 2 o'clock (−60° to +60°). Both rows have the same angular limits. The outer row is physically longer. Keep text inside this sector and truncate overflow with `...`. Indent from the screen edge should visually match the battery sectors.
- Weather stays visible independently of calendar events. Three samples: current, approximately +3 hours, approximately +6 hours, showing actual forecast times, temperature, and weather symbol. Do not use percentage text for rain. Future probability gradations can be encoded with distinguishable symbols; the current prototype only demonstrates weather symbols and does not implement a probability mapping.
- Health information is lower left; battery indicators are lower right.
- Steps: large footprints icon → radial progress sector → current step count. No goal number or textual percentage. Progress visually communicates proximity to the configured daily goal. Reserve space for five digits plus a thousands separator.
- Batteries: watch uses the inner sector; phone uses the outer sector. Device icon → radial progress sector → numeric percentage. Icons, arc fill, and number share the status color.
- All three sector heads and their icons align visually. Progress fills from the icon end toward the numeric end, and shrinks toward the icon as battery charge falls.
- Numbers for steps and batteries use Courier New monospace terminal styling, follow their arcs, and are centered radially on the arc centerline rather than sitting on an outer baseline.
- Compass has a thin rim, cardinal labels, and a lower gap with curved heading text such as `NE · 042°`. Heading text follows the circle rather than a horizontal baseline.
- Fixed hour markers sit along the inner edge of the compass rim, amber like the hour/minute hands. Omit the 6 o'clock marker to leave room for heading text. They are short marks, not hour numbers. Keep compass rotation conceptually separate from the fixed time markers.
- Pulse: three-digit number below a filled heart, enclosed in a circular outline. Center the heart and numeral group inside the circle. Heart fill indicates HR zone; pulse digits remain green. No BPM label.
- AOD retains only digital time, date, and all three weather samples at lower brightness. Analog hands, calendar, pulse, steps, battery sectors, compass, and hour marks disappear. No second-hand animation in AOD. The preview still draws a dim outer decorative bezel.

## Latest geometry (480 × 480 logical units)

Use the HTML/SVG as the precise reference. Angles in sector descriptions are clockwise from 12 o'clock unless explicitly stated otherwise.

| Element | Current parameter |
| --- | --- |
| Face and hand pivot | (240, 240) |
| Screen clip | radius 231 |
| Compass rim | radius 218 |
| Fixed hour marks | radii 211–218, width 2, amber at opacity 0.85 |
| Date | center x 240, baseline y 119; Courier New 25, bold, letter spacing 2 |
| Main digital time | center x 240, baseline y 221.5; Arial Narrow / Liberation Sans Narrow / Arial fallback, 115.434, bold, letter spacing −4 |
| Event outer row | radius 182; font 17.5 Courier New bold; angular character advance 3.3°; sample capacity 36 |
| Event inner row | radius 161; font 16 Courier New bold; angular character advance 3.5°; sample capacity 34 |
| Weather labels | x 136 / 240 / 344, baseline 273; Courier New 19 bold |
| Weather temperatures | x 155 / 259 / 363, baseline 307; font 28 bold |
| Weather icons | 31.5 × 31.5 logical-unit boxes; explicit SVG |
| Pulse circle | center (195, 364), radius 42, outline width 1.2 |
| Pulse digits | local anchor (186, 384) in a group translated (9,9); font 40, horizontal scale 0.82 |
| Heart | box x 171.312, y 320.312, 29.376 × 29.376, in the same translated group |
| Steps sector | radius 194; angles 261° → 209°, counterclockwise; width 9 |
| Phone battery sector | radius 194; angles 99° → 158°, clockwise; width 9 |
| Watch battery sector | radius 166; angles approximately 100.536° → 158°, clockwise; width 9 |
| Steps/battery numbers | font 21, Courier New bold, dominant-baseline central |
| Hour / minute / second hands | widths 4 / 2.4 / 0.8; hour/minute opacity 0.85 |
| Heading text | radius 226; Courier New 17; curved individual glyphs |

Sector tracks use the corresponding fill color at opacity 0.16. Caps are round. Current progress uses stroke-dasharray in the prototype. All icons are directly editable SVG; there are no external icon assets to scale.

## Palette

| Meaning | Color |
| --- | --- |
| Screen | `#020704` |
| Main phosphor green, healthy battery | `#91F894` |
| Structure | `#3F7046` |
| Pulse outline / supporting green | `#68B974` |
| Amber hands, hour marks, low battery | `#FFC15C` |
| Bright red second hand | `#FF3939` |
| Proposed critical battery | `#E76F51` |
| AOD text and weather | `#579B5D` |

Proposed charge mapping for BOTH devices: 31–100% green; 11–30% amber; 0–10% warm red. These thresholds are a design proposal, not OS settings. Color belongs to charge level, not device identity.

## Heart-rate zones

The user's screenshot selects heart-rate reserve (HRR). Its displayed relative boundaries are 0 / 30 / 40 / 60 / 90 / 100 percent. Treat these as the reference/configurable thresholds, not a universal physiological prescription.

| Zone | Screenshot interval (%HRR) | Prototype heart color |
| --- | --- | --- |
| 1 | 0–30 | `#409EF8` blue |
| 2 | 30–40 | `#55B52C` green |
| 3 | 40–60 | `#F4B400` yellow |
| 4 | 60–90 | `#FF730D` orange |
| 5 | 90–100 | `#E52520` red |

Use an unfilled green outline when no zone data is available. The exact colors approximate the screenshot. If calculating HRR, use configured/resting and maximum HR: `(currentHR - restingHR) / (maxHR - restingHR) * 100`. Do not infer a genuine HR zone from current HR alone. The screenshot does not supply the required resting/max values. The sample 128 and yellow zone 3 are an explicitly selected visual demonstration.

For deterministic software intervals, assign an exact boundary to the higher zone (30 → 2, 40 → 3, 60 → 4, 90 → 5), subject to the authoritative provider/configuration. Handle invalid/missing/stale inputs explicitly rather than silently treating them as a valid zone. A directly supplied authoritative zone can be used without recalculating it.

## Sample data

- Digital and analog time 10:09, seconds 24 at initial render.
- Date SUN 11.
- Event `18:00 · Quick DS+GL Business Update: Strategy and Integration Progress`.
- Other event selector examples: SDV Leads Daily Stand Up, Project Alignment Meeting, DAC - Dev Daily Sync.
- Weather NOW 12° partly cloudy; 13:00 14° drizzle; 16:00 13° rain.
- Pulse 128, demo zone 3 yellow.
- Steps 6,240 / 8,000 → 78% progress, goal hidden on screen.
- Inner watch battery 15%, amber; outer phone battery 84%, green.
- Heading NE · 042°.

## Known issues and implementation work

1. Long calendar text currently intersects the digital time at the left/right ends of the upper sector in active mode. This was observed and disclosed before export. Resolve layout without dropping the two-row radial design or silently shrinking its sector. The current version is a working design reference, not a finalized collision-free production layout.
2. Most readings, heading, hour/minute hands, forecast timestamps, and date are sample/static. The second hand advances once per second, and preview controls demonstrate local changes. Implement synchronized real clocks and providers in the target system.
3. Calendar wrapping uses character limits as a prototype approximation. Production must measure the chosen embedded font against each arc's usable length, preserve angular boundaries, and handle long words, Unicode, and overflow reliably.
4. The selected fonts are fallbacks rather than bundled assets. Choose and embed suitable licensed equivalents; ensure appearance and width remain stable on the device. Digital time intentionally uses a large condensed readable font, while curved values and labels use terminal monospace styling.
5. Source paths are 480 × 480 logical coordinates; scale to the actual device surface. Verify both active/AOD on the target watch, including appropriate AOD rendering and update rules for that platform.
6. No native watchface framework, complication support, companion phone bridge, sensor access, weather backend, permissions, battery policy, or installation pipeline has been implemented or verified. Research the actual device's supported watchface/data APIs before choosing architecture. Do not assume Samsung Health zones, calendar names, full three-point weather, phone battery, or live compass are all exposed directly to a watchface.
7. Decide how to distinguish stale versus fresh readings in the native implementation; the design prototype does not establish this behavior.

## Visual verification targets

- No overlaps/clipping in both modes, including time 23:59, 5-digit steps, batteries 100%, pulse 3 digits, long calendar names, and negative/two-digit temperatures.
- Outer calendar row physically longer than inner; neither crosses its angular boundary.
- Heart and pulse remain balanced within the circle for all zone colors.
- Low-charge watch stays amber at 15%; full-length sectors and numeric values agree.
- AOD shows only time/date/weather and stops unnecessary animation.
- Hour marks stay fixed while compass rotates according to actual heading.
