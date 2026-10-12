# Calendar layout — 2026-10-12

Current production geometry: concentric baseline radii 194/173, font size 20
and CENTER alignment on both arcs, angles −60…+60. The previous 180/159
radii left unused outer space and brought the inner row too close to the clock.
The longer outer arc now fits more of the actual event on the first row.
Measured capacities are 33/30. Word-boundary wrapping and native final-row
ellipsis are retained.

The shared rendering/touch BoundingArc expands from outer radius 196 to 210
(thickness 50, inner radius 160) so Samsung does not clip the shifted glyphs.
This supersedes the former radius-196 status-indicator clearance constraint
in docs/tap-targets.md; the arc follows the requested outward text placement.

Validation: all 40 Python tests pass, including two-pixel-margin clock
collision checks, expanded clipping checks, and unchanged font size checks.
Android lint/build succeeded. APK installation returned Success. Physical
screenshots artifacts/calendar-radius-before.png and calendar-radius-after.png
show the same actual 18:00 GlobalLogic Sport Club event before and after:
the first row now includes Sport Club and the second row sits farther outward.
The original generator and APK are preserved in artifacts for rollback.

## Previous layout notes (historical)

### 2026-10-11

Latest user adjustment: font size 20 on both arcs, CENTER alignment on
each arc, radii 194/173 retained. First-row capacity is 33 (inner nominal
capacity 30). First-row wrapping still chooses the last complete word that
fits. The inner row now receives the complete remainder and uses native
TextCircular ellipsis, rather than discarding an entire last word before
rendering. This avoids unnecessary empty space and uses shaped glyph widths.
No manual UTF-16 cut inside the final word is introduced in WFF. Native
handling of complex emoji/font fallback is not established by host tests.
Main time remains 115.434: two-pixel-margin collision checks pass.
Current preview: `artifacts/calendar-20px-centered-preview.png` (synthetic).

## Original restoration (superseded geometry below)

The handoff event renders as:

```
18:00 · Quick DS+GL Business Update:
Strategy and Integration Progress
```

Production WFF restores concentric baseline radii 182/161, font sizes 17.5/16,
angles −60…+60 and START alignment. The outer row starts at the left edge;
the inner row starts at the same angular boundary. The embedded font remains
Liberation Mono Bold (licensed substitute for Courier New).

The two capacities 36/35 are calculated from the actual embedded monospace
font advances and each arc length. Ordered WFF Condition/Compare branches
select the last fitting space/NBSP for the first break. The second row keeps
whole words and appends `...` when content exceeds its measured budget.
No manual substring boundary falls inside a word or emoji sequence. An
unbroken word too long for both available rows is represented by `...`.
Tabs, explicit newlines, hyphenation and a full emoji font are not implemented.

Main time size 115.434 matches the handoff. This resolves the calendar/time
collision without moving the calendar toward the compass rim or narrowing
its sector. The calendar BoundingRoundBox is (50,22,380,160), expanded from
height 110 to cover restored text down to y159. Samsung can clip rendering
at complication bounds; the host render alone previously missed this.

Tests execute the generated WFF expressions, not a duplicate wrapping
algorithm. Coverage includes the handoff event, short/missing titles, long
Ukrainian words, long unbroken text, emoji strings, overflow and geometry.
Pixel masks for 00:00, 23:59 and 10:09 have no calendar/time overlap, including
a two-pixel calendar margin. The host renderer now preserves fractional
font sizes rather than rounding 17.5 to 18 and introducing false ellipsis.

`artifacts/calendar-handoff-restored.png` is a synthetic host preview, not
proof of a real event on the watch. APK installation and successful schema,
build, lint and memory checks do not establish actual start-time delivery.
The system NEXT_EVENT provider binding is retained. A physical active screenshot now confirms a system calendar event with
20:00 start time and a long Ukrainian name on both arcs. The exact raw
TEXT/TITLE split remains redacted in the runtime dump. Weather recovery is
an independent unresolved issue; this change does not fix it.

Official WFF references:
- [Condition uses the first matching Compare](https://developer.android.com/training/wearables/wff/transform/content)
- [String operations](https://developer.android.com/reference/wear-os/wff/common/attributes/arithmetic-expression)

Validation: 24 Python tests, Android lint/build, official WFF3 schema and
APK memory-footprint checks pass. Final APK installation returned Success.

Physical evidence: `artifacts/device-calendar-restored.png` shows the
updated active face with the actual calendar event, both complete arc starts
and no overlap with main time18:06. The preceding natural AOD screenshot
correctly hid calendar content. Weather remains unavailable on both captures.

Native CENTER/ellipsis attributes: [WFF TextCircular](https://developer.android.com/reference/wear-os/wff/group/part/text/text-circular).

Physical verification of the latest font20/CENTER build: install returned
Success; `artifacts/device-calendar-20-centered.png` shows the real20:00
event with both centered arcs. The inner row fills the arc through a
partial final word plus native ellipsis. No visible main-time or hour-mark
overlap. All24 Python tests, Android lint/build, WFF3 schema and memory
checks passed. Weather remains unavailable, independently of this change.
