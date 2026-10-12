# Pip-Boy watchface — design handoff

This is the latest collaboratively reviewed visual prototype, exported on 2026-10-11. It is a design reference, not a working Wear OS watchface. Sample readings are illustrative.

## Files

- `preview.html`: standalone interactive preview, initially in AOD. Open locally in a browser. Toggle AOD to inspect active mode. Controls also change sample time, calendar event, and heart-rate zone.
- `prototype-fragment.html`: editable source used during the design conversation. All product icons are authored inline SVG.
- `active.svg`, `aod.svg`: editable static vector references at a 480 × 480 coordinate system.
- `active.png`, `aod.png`: rendered references at 480 × 480. SVG rendering and font substitution may differ from the target device; compare with the interactive preview.
- `DESIGN.md`: accepted design decisions, current dimensions, known issues, and implementation requirements.
- `PROMPT.md`: task text to give Codex after extracting this folder into the project.

## Continue in Codex

Extract this folder into your repository, for example `design/watchface/`. Give Codex the text in `PROMPT.md`, changing its folder path if needed. The editable HTML/SVG and design requirements should be used together.

The current design has a known collision between long radial calendar text and the edges of the large digital time. Preserve the intent of the radial sector and resolve this collision during implementation; do not silently discard calendar content or alter the overall layout.

These files do not select or implement a Wear OS framework. Check the actual target device, installed OS, available watchface APIs, and data providers before choosing the production architecture.
