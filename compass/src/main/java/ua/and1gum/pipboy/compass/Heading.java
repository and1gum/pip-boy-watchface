package ua.and1gum.pipboy.compass;

import java.util.Locale;

final class Heading {
    private static final String[] DIRECTIONS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
    private static final String[] LABELS = new String[360];
    private Heading() {}
    static int degrees(double value) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException("Invalid sensor heading");
        return (int) ((Math.round(value) % 360 + 360) % 360);
    }
    static String label(int degrees) {
        int normalized = degrees(degrees);
        String label = LABELS[normalized];
        if (label == null) {
            label = String.format(Locale.US, "%s · %03d°", DIRECTIONS[((normalized + 22) / 45) % 8], normalized);
            // Concurrent misses can duplicate formatting, but only immutable strings
            // for this same normalized heading are stored in each bounded entry.
            LABELS[normalized] = label;
        }
        return label;
    }
}
