# Samsung/WFF animation investigation, 2026-10-11

The current question is where intermediate compass frames should be generated:
in the watch-face renderer or by repeated public complication updates. A higher
sensor sampling rate alone does not answer this question.

## Verified public approaches

* Samsung WFS Gyro effects map wrist tilt on the X/Y axes (-90 to +90 degrees)
  into rotation, displacement, scale and opacity. These are not magnetic heading
  sources. [Samsung guide](https://developer.samsung.com/watch-face-studio/user-guide/gyro.html).
* Samsung's animation tutorial describes prerecorded image sequences, GIF and
  WebP, with wake, tap and interval triggers. Its 15 fps statement belongs to
  that 2023 tutorial, not a proven universal limit on today's WFF renderer.
  A prerecorded sequence cannot itself follow live magnetic heading.
  [Samsung tutorial](https://developer.samsung.com/sdp/blog/en/2023/11/02/using-animation-to-create-dynamic-watch-faces).
* WFF Transform/Animation explicitly interpolates changing attributes. Its
  angleDirection defaults to NONE, documented as "No angular rotation";
  CLOCKWISE and COUNTER_CLOCKWISE select angular directions. This is a useful
  diagnostic difference, not yet proof of our problem. Forcing one direction
  in a bidirectional compass could cause unwanted long rotations.
  [Animation reference](https://developer.android.com/reference/wear-os/wff/common/transform/animation),
  [official position-animation example](https://developer.android.com/training/wearables/wff/transform).
* Samsung recommends limiting frequently updating complications for performance
  and power efficiency. Sending intermediate values at 30 Hz is an experimental
  fallback, not established as an efficient production solution.
  [Optimization guide](https://developer.samsung.com/codelab/watch-face-studio/design-optimization.html).

Previously inspected installed Samsung Ultra code reads SensorManager inside
its executable face, unlike our resource-only WFF plus separate provider. This
explains an architectural difference; it does not establish the exact Samsung
frame scheduling/filtering algorithm, or prove a third-party exclusivity rule.

## Controlled diagnostic

`python3 scripts/probe_animation.py /tmp/pip-boy-animation-probe.xml` writes a
temporary diagnostic XML without changing release sources. It preserves slot
declaration order and compares three identical two-second target changes:

1. Group angle 0/90, angleDirection=NONE.
2. Group angle 0/90, angleDirection=CLOCKWISE.
3. Group x position over 30 pixels.

Each has a one-second LINEAR animation at 30 fps, an explicit initial angle, and
an ambient-hidden marker. One row is directly in Scene; the other is inside
the stable phone-battery RANGED_VALUE complication, whose bound is temporarily
expanded to avoid clipping. This isolates time-driven rendering from heading
measurement and compass-provider delivery. It does not prove behavior under
continuous retargeting or inside the compass slot itself.

The diagnostic APK is temporary and must be replaced by the release APK after
recording. Do not distribute it as the finished face.

## Physical control result

The first capture was covered by a notification. The second exposed an error in
the diagnostic itself: a helper nested PartDraw inside PartDraw, hiding markers.
Neither is evidence against WFF animation. Corrected diagnostic XML passed the
official WFF 3 validator before the third capture.

The corrected control recorded 203 frames over 14.69 seconds, with a median
frame interval of 34.0 ms. Visual frames show intermediate angles in both rows.
Amber-marker ROI/PCA analysis found 67 distinct rounded angles for Scene/NONE
and 69 for complication/NONE, spanning 0–90 degrees. CLOCKWISE also animates,
including the expected longer return path. The angleDirection=NONE hypothesis
is therefore rejected on this device. Frame recording cadence is not a panel
refresh-rate measurement.

This establishes that the device can interpolate Group angle transforms inside
a stable complication. It does not yet isolate why frequently replaced compass
payloads did not interpolate in earlier captures. The next useful control is a
stable payload versus repeated identical and changed payloads, with the same
animation, rather than raising sensor frequency. The diagnostic was removed;
the release watch-face APK reinstalled with Success. Final provider APK also
installed with Success. The 30 Hz provider remains experimental, without a
verified live-compass smoothness or battery result.
