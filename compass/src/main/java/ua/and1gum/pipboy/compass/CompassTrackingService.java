package ua.and1gum.pipboy.compass;

import android.app.KeyguardManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.ServiceInfo;
import android.hardware.display.DisplayManager;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.util.Log;
import android.view.Display;
import android.view.WindowManager;

/** Foreground lifetime permits background sensors; no wake lock or asleep polling. */
public final class CompassTrackingService extends Service implements DisplayManager.DisplayListener {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private CompassSensor sensor;
    private DisplayManager displays;
    private float published = Float.NaN;
    private final HeadingMotion motion = new HeadingMotion();
    private long publishedAt;
    private boolean hadFreshData;
    // Some watches keep the display ON through ambient mode and omit an unlock broadcast.
    // Recheck eligibility without reading sensors or holding a wake lock while paused.
    private final Runnable retryWhenEligible = this::refresh;
    private final Runnable tick = new Runnable() {
        @Override public void run() {
            refresh();
            if (CompassState.reading) {
                publishReading();
                handler.postDelayed(this, 33);
            }
        }
    };
    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) { refresh(); }
    };
    static void start(Context context) {
        if (!CompassState.enabled(context) || !CompassState.hasSlots(context)) return;
        try { context.startForegroundService(new Intent(context, CompassTrackingService.class)); }
        catch (RuntimeException denied) {
            Log.w("PipBoyCompass", "Open Pip-Boy Compass once to enable tracking", denied);
        }
    }
    @Override public void onCreate() {
        super.onCreate();
        NotificationManager nm = getSystemService(NotificationManager.class);
        nm.createNotificationChannel(new NotificationChannel("compass", "Compass tracking", NotificationManager.IMPORTANCE_LOW));
        PendingIntent open = PendingIntent.getActivity(this, 0, new Intent(this, CompassActivity.class), PendingIntent.FLAG_IMMUTABLE);
        PendingIntent stop = PendingIntent.getService(this, 1,
                new Intent(this, CompassTrackingService.class).setAction("STOP"), PendingIntent.FLAG_IMMUTABLE);
        Notification notification = new Notification.Builder(this, "compass")
                .setSmallIcon(android.R.drawable.ic_menu_compass).setContentTitle("Pip-Boy Compass")
                .setContentText("Sensors pause when the display sleeps or locks")
                .setContentIntent(open).setOngoing(true)
                .addAction(new Notification.Action.Builder(null, "Stop", stop).build()).build();
        startForeground(1, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        WindowManager wm = getSystemService(WindowManager.class);
        sensor = new CompassSensor(this, wm.getDefaultDisplay().getRotation(), (degrees, accuracy) -> {
            if (accuracy >= 1) motion.target(sensor.continuousHeading(), SystemClock.elapsedRealtime());
            CompassState.accuracy = accuracy;
            CompassState.measuredAt = SystemClock.elapsedRealtime();
            publishReading();
        });
        displays = getSystemService(DisplayManager.class);
        displays.registerDisplayListener(this, handler);
        IntentFilter filter = new IntentFilter(Intent.ACTION_SCREEN_ON);
        filter.addAction(Intent.ACTION_SCREEN_OFF);
        filter.addAction(Intent.ACTION_USER_PRESENT);
        registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED);
    }
    private boolean allowed() {
        Display display = displays.getDisplay(Display.DEFAULT_DISPLAY);
        return TrackingPolicy.shouldRead(CompassState.enabled(this), CompassState.hasSlots(this),
                getSystemService(PowerManager.class).isInteractive(),
                display != null && display.getState() == Display.STATE_ON,
                !getSystemService(KeyguardManager.class).isKeyguardLocked());
    }
    private void refresh() {
        Display currentDisplay=displays.getDisplay(Display.DEFAULT_DISPLAY);
        if (currentDisplay != null && sensor.setRotation(currentDisplay.getRotation())) {
            motion.reset();
            published = Float.NaN;
            CompassState.measuredAt = 0;
            hadFreshData = false;
            CompassSource.requestUpdate(this);
        }
        boolean allowed = allowed();
        if (allowed && !CompassState.reading) {
            published = Float.NaN;
            hadFreshData = false;
            CompassState.reading = sensor.start();
            Log.i("PipBoyCompass", "Sensor started=" + CompassState.reading);
            handler.removeCallbacks(tick);
            if (CompassState.reading) handler.postDelayed(tick, 33);
        } else if (!allowed && CompassState.reading) {
            pause();
        }
        if (!CompassState.enabled(this) || !CompassState.hasSlots(this)) stopSelf();
        handler.removeCallbacks(retryWhenEligible);
        if (!CompassState.reading && CompassState.enabled(this) && CompassState.hasSlots(this))
            handler.postDelayed(retryWhenEligible, 10_000);
    }
    private void publishReading() {
        long now = SystemClock.elapsedRealtime();
        if (!CompassState.fresh()) {
            if (hadFreshData) { hadFreshData = false; CompassSource.requestUpdate(this); }
            return;
        }
        CompassState.continuousHeading = (float) motion.sample(now);
        CompassState.heading = Heading.degrees(CompassState.continuousHeading);
        if (TrackingPolicy.shouldPublish(published, CompassState.continuousHeading, publishedAt, now)) {
            published = CompassState.continuousHeading;
            publishedAt = now;
            hadFreshData = true;
            CompassSource.requestUpdate(this);
            Log.d("PipBoyCompass", "Push heading=" + published);
        }
    }
    private void pause() {
        handler.removeCallbacksAndMessages(null);
        sensor.stop();
        motion.reset();
        CompassState.clear();
        hadFreshData = false;
        published = Float.NaN;
        CompassSource.requestUpdate(this);
        Log.i("PipBoyCompass", "Sensor stopped; no polling while display inactive");
    }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && "STOP".equals(intent.getAction())) CompassState.enable(this, false);
        refresh();
        return START_STICKY;
    }
    @Override public void onDisplayChanged(int id) { if (id == Display.DEFAULT_DISPLAY) refresh(); }
    @Override public void onDisplayAdded(int id) {}
    @Override public void onDisplayRemoved(int id) { refresh(); }
    @Override public IBinder onBind(Intent intent) { return null; }
    @Override public void onDestroy() {
        displays.unregisterDisplayListener(this);
        unregisterReceiver(receiver);
        pause();
        super.onDestroy();
    }
}
