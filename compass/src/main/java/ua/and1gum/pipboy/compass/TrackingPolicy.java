package ua.and1gum.pipboy.compass;

/** Shared, testable rules for sensor power and public push update cadence. */
final class TrackingPolicy {
    private TrackingPolicy() {}
    static boolean shouldRead(boolean enabled, boolean hasSlots, boolean displayOn, boolean unlocked) {
        // Wrist-raise can turn the display ON while PowerManager is still non-interactive.
        return enabled && hasSlots && displayOn && unlocked;
    }
    static boolean shouldPublish(float last, float current, long lastTime, long now) {
        return Float.isNaN(last) || now - lastTime >= 4000 || (Math.abs(current-last) >= 0.03f && now - lastTime >= 33);
    }
    static boolean isFresh(long timestamp, long now, int accuracy) {
        return timestamp > 0 && now >= timestamp && now - timestamp < 5000 && accuracy >= 1;
    }
}
