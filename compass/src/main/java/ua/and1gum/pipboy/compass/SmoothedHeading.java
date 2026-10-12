package ua.and1gum.pipboy.compass;
/** Time-based circular low-pass filter; continuous turns avoid 359-to-0 animation spins. */
final class SmoothedHeading {
    private boolean initialized;
    private double value;
    private long measuredAt;
    double update(double raw,long now) {
        if (!initialized) { initialized=true; value=raw; }
        else {
            double delta=((raw-value)%360+540)%360-180;
            double alpha=1-Math.exp(-Math.max(0,now-measuredAt)/100.0);
            value+=alpha*delta;
        }
        measuredAt=now;
        return value;
    }
    void reset() { initialized=false; }
}
