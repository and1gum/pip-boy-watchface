package ua.and1gum.pipboy.compass;

import java.util.Locale;

final class Heading {
    private Heading() {}
    static int degrees(double value) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException("Invalid sensor heading");
        return (int) ((Math.round(value) % 360 + 360) % 360);
    }
    static String label(int degrees) {
        String[] directions = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
        int normalized = degrees(degrees);
        return String.format(Locale.US, "%s · %03d°", directions[((normalized + 22) / 45) % 8], normalized);
    }
}
