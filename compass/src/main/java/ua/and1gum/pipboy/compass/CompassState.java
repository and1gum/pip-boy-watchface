package ua.and1gum.pipboy.compass;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.SystemClock;
import java.util.HashSet;
import java.util.Set;

/** Runtime readings are never restored from disk as if they were fresh. */
final class CompassState {
    static volatile int heading;
    static volatile float continuousHeading;
    static volatile int accuracy;
    static volatile long measuredAt;
    static volatile boolean reading;
    private CompassState() {}
    static SharedPreferences preferences(Context context) {
        return context.getSharedPreferences("compass", Context.MODE_PRIVATE);
    }
    static boolean enabled(Context context) { return preferences(context).getBoolean("enabled", true); }
    static void enable(Context context, boolean enabled) {
        preferences(context).edit().putBoolean("enabled", enabled).apply();
    }
    static boolean hasSlots(Context context) {
        return !preferences(context).getStringSet("slots", Set.of()).isEmpty();
    }
    static void slot(Context context, int id, boolean active) {
        Set<String> slots = new HashSet<>(preferences(context).getStringSet("slots", Set.of()));
        boolean changed = active ? slots.add(Integer.toString(id)) : slots.remove(Integer.toString(id));
        if (changed) preferences(context).edit().putStringSet("slots", slots).apply();
    }
    static boolean fresh() {
        return reading && TrackingPolicy.isFresh(measuredAt, SystemClock.elapsedRealtime(), accuracy);
    }
    static void clear() { measuredAt = 0; accuracy = 0; reading = false; }
}
