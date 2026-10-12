package ua.and1gum.pipboy.compass;

/** Android pressure sensors report hPa; display whole millimeters of mercury. */
final class PressureUnits {
    static String millimeters(double hectopascals) {
        return Long.toString(Math.round(hectopascals * 0.750061683));
    }
}
