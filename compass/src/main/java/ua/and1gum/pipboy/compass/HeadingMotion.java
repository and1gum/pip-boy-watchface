package ua.and1gum.pipboy.compass;
/** Continuous visual motion between sensor targets, independent of sensor sampling. */
final class HeadingMotion {
 private boolean initialized;
 private double position, destination;
 private long updatedAt;
 void target(double value,long now) {
  if (!initialized) { position=value; initialized=true; updatedAt=now; }
  else sample(now);
  destination=value;
 }
 double sample(long now) {
  if (!initialized) return Double.NaN;
  long elapsed=Math.max(0,now-updatedAt);
  position += (destination-position)*(1-Math.exp(-elapsed/120.0));
  updatedAt=now;
  return position;
 }
 void reset() { initialized=false; }
}
