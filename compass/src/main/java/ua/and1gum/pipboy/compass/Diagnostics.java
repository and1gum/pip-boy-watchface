package ua.and1gum.pipboy.compass;

import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Process;
import android.os.SystemClock;
import android.app.KeyguardManager;
import android.hardware.Sensor;
import android.hardware.SensorManager;
import android.hardware.display.DisplayManager;
import android.view.Display;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/** Explicit, process-local collection. No timers, listeners, wake locks or automatic writes. */
final class Diagnostics {
    private static volatile DiagnosticSession session;
    private Diagnostics() {}

    static boolean enabled() {
        DiagnosticSession current = session;
        return current != null && current.isRecording() && current.active(SystemClock.elapsedRealtime());
    }
    static void start(Context context) {
        String version;
        try { version = context.getPackageManager().getPackageInfo(context.getPackageName(), 0).versionName; }
        catch (PackageManager.NameNotFoundException unavailable) { version = "unknown"; }
        DiagnosticSession fresh = new DiagnosticSession();
        fresh.start(SystemClock.elapsedRealtime(), System.currentTimeMillis(),
                version + ";pid=" + Process.myPid() + ";sdk=" + Build.VERSION.SDK_INT);
        session = fresh;
        Display display = context.getSystemService(DisplayManager.class).getDisplay(Display.DEFAULT_DISPLAY);
        int gates = (CompassState.enabled(context) ? 1 : 0) | (CompassState.hasSlots(context) ? 2 : 0)
                | (display != null && display.getState() == Display.STATE_ON ? 4 : 0)
                | (!context.getSystemService(KeyguardManager.class).isKeyguardLocked() ? 8 : 0);
        event("initialGates", gates);
        event("initialReading", CompassState.reading ? 1 : 0);
        event("samplingDelayHint", SensorManager.SENSOR_DELAY_UI);
        SensorManager sensors = context.getSystemService(SensorManager.class);
        Sensor sensor = sensors.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
        if (sensor == null) sensor = sensors.getDefaultSensor(Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR);
        if (sensor != null) {
            event("sensorType", sensor.getType());
            event("sensorMinDelayUs", sensor.getMinDelay());
            event("sensorReportedPowerUa", Math.round(sensor.getPower() * 1000));
        }
    }
    static void stop() {
        DiagnosticSession current = session;
        if (current != null && current.isRecording()) current.stop(SystemClock.elapsedRealtime());
    }
    static void event(String name, long value) {
        DiagnosticSession current = session;
        if (current != null && current.isRecording()) current.event(SystemClock.elapsedRealtime(), name, value);
    }
    static void count(String name) {
        DiagnosticSession current = session;
        if (current != null && current.isRecording()) current.count(SystemClock.elapsedRealtime(), name);
    }
    /** Explicit technical export, readable using adb shell run-as for the current debug build. */
    static File export(Context context) throws IOException {
        DiagnosticSession current = session;
        String json = current == null ? "{\"recorded\":false}"
                : current.json(current.isRecording() ? SystemClock.elapsedRealtime() : 0);
        File output = new File(context.getFilesDir(), "diagnostics.json");
        try (FileOutputStream stream = new FileOutputStream(output)) {
            stream.write(json.getBytes(StandardCharsets.UTF_8));
        }
        return output;
    }
}
