package ua.and1gum.pipboy.compass;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.SystemClock;
import android.view.Surface;

/** Magnetic heading of the top of the screen; no location or network access. */
final class CompassSensor implements SensorEventListener {
    interface Listener { void onHeading(int degrees, int accuracy); }
    private final SensorManager manager;
    private final Sensor sensor;
    private final Listener listener;
    private int rotation;
    private final SmoothedHeading filter = new SmoothedHeading();
    private float continuous;
    private long timestamp;
    private int heading;
    private int accuracy = SensorManager.SENSOR_STATUS_UNRELIABLE;
    private boolean registered;

    CompassSensor(Context context, int rotation, Listener listener) {
        this.manager = (SensorManager) context.getSystemService(Context.SENSOR_SERVICE);
        Sensor preferred = manager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
        this.sensor = preferred != null ? preferred : manager.getDefaultSensor(Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR);
        this.rotation = rotation;
        this.listener = listener;
    }
    boolean setRotation(int rotation) {
        if (this.rotation == rotation) return false;
        this.rotation=rotation; filter.reset(); return true;
    }
    float continuousHeading() { return continuous; }
    boolean start() {
        if (registered) return true;
        registered = sensor != null && manager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_UI);
        return registered;
    }
    void stop() {
        manager.unregisterListener(this);
        registered = false;
        timestamp = 0;
        filter.reset();
    }
    boolean isFresh() {
        return timestamp != 0 && SystemClock.elapsedRealtime() - timestamp < 5000
                && accuracy >= SensorManager.SENSOR_STATUS_ACCURACY_LOW;
    }
    int heading() { return heading; }
    @Override public void onSensorChanged(SensorEvent event) {
        accuracy = event.accuracy;
        float[] matrix = new float[9];
        SensorManager.getRotationMatrixFromVector(matrix, event.values);
        float[] remapped = new float[9];
        int x = SensorManager.AXIS_X, y = SensorManager.AXIS_Y;
        if (rotation == Surface.ROTATION_90) { x = SensorManager.AXIS_Y; y = SensorManager.AXIS_MINUS_X; }
        if (rotation == Surface.ROTATION_180) { x = SensorManager.AXIS_MINUS_X; y = SensorManager.AXIS_MINUS_Y; }
        if (rotation == Surface.ROTATION_270) { x = SensorManager.AXIS_MINUS_Y; y = SensorManager.AXIS_X; }
        SensorManager.remapCoordinateSystem(matrix, x, y, remapped);
        float[] orientation = new float[3];
        SensorManager.getOrientation(remapped, orientation);
        double degrees = Math.toDegrees(orientation[0]);
        if (!Double.isFinite(degrees)) return;
        timestamp = SystemClock.elapsedRealtime();
        if (accuracy >= SensorManager.SENSOR_STATUS_ACCURACY_LOW) {
            continuous = (float) filter.update(degrees < 0 ? degrees + 360 : degrees, timestamp);
            heading = Heading.degrees(continuous);
        }
        listener.onHeading(heading, accuracy);
    }
    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) { this.accuracy = accuracy; }
}
