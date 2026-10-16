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
import android.os.Build;
import android.os.IBinder;
import android.os.Looper;
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
    private KeyguardManager keyguard;
    private int diagnosticGates = -1;
    private boolean awaitingFirstSample;
    // Some watches omit an unlock broadcast when leaving ambient mode.
    // Recheck eligibility without reading sensors or holding a wake lock while paused.
    private final Runnable retryWhenEligible = this::refresh;
    private final Runnable tick = new Runnable() {
        @Override public void run() {
            Diagnostics.count("tick");
            refresh();
            if (CompassState.reading) {
                publishReading();
                handler.postDelayed(this, 33);
            }
        }
    };
    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (Diagnostics.enabled()) Diagnostics.event(intent.getAction() == null ? "screenBroadcast" : intent.getAction(), 0);
            refresh();
        }
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
            Diagnostics.count("sensorSample");
            if (accuracy >= 1) motion.target(sensor.continuousHeading(), SystemClock.elapsedRealtime());
            CompassState.accuracy = accuracy;
            CompassState.measuredAt = SystemClock.elapsedRealtime();
            if (awaitingFirstSample && accuracy >= 1) {
                awaitingFirstSample = false;
                Diagnostics.event("firstAccurateSample", accuracy);
            }
            publishReading();
        });
        displays = getSystemService(DisplayManager.class);
        keyguard = getSystemService(KeyguardManager.class);
        if (Build.VERSION.SDK_INT >= 36) {
            // State-only changes (including wrist-raise while dreaming) need an explicit
            // subscription on newer Android; the legacy overload omits this event.
            displays.registerDisplayListener(getMainExecutor(),
                    DisplayManager.EVENT_TYPE_DISPLAY_ADDED | DisplayManager.EVENT_TYPE_DISPLAY_REMOVED
                            | DisplayManager.EVENT_TYPE_DISPLAY_CHANGED | DisplayManager.EVENT_TYPE_DISPLAY_STATE,
                    this);
        } else {
            displays.registerDisplayListener(this, handler);
        }
        IntentFilter filter = new IntentFilter(Intent.ACTION_SCREEN_ON);
        filter.addAction(Intent.ACTION_SCREEN_OFF);
        filter.addAction(Intent.ACTION_USER_PRESENT);
        registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED);
    }
    private void refresh() {
        Diagnostics.count("refresh");
        Display currentDisplay=displays.getDisplay(Display.DEFAULT_DISPLAY);
        boolean enabled = CompassState.enabled(this);
        boolean hasSlots = CompassState.hasSlots(this);
        boolean displayOn = currentDisplay != null && currentDisplay.getState() == Display.STATE_ON;
        boolean unlocked = !keyguard.isKeyguardLocked();
        if (Diagnostics.enabled()) {
            int gates = (enabled ? 1 : 0) | (hasSlots ? 2 : 0) | (displayOn ? 4 : 0) | (unlocked ? 8 : 0);
            if (gates != diagnosticGates) { diagnosticGates = gates; Diagnostics.event("gates", gates); }
        }
        if (currentDisplay != null && sensor.setRotation(currentDisplay.getRotation())) {
            motion.reset();
            published = Float.NaN;
            CompassState.measuredAt = 0;
            hadFreshData = false;
            CompassSource.requestUpdate(this);
        }
        boolean allowed = TrackingPolicy.shouldRead(enabled, hasSlots, displayOn, unlocked);
        if (allowed && !CompassState.reading) {
            published = Float.NaN;
            hadFreshData = false;
            awaitingFirstSample = true;
            CompassState.reading = sensor.start();
            Diagnostics.event("sensorStart", CompassState.reading ? 1 : 0);
            handler.removeCallbacks(tick);
            if (CompassState.reading) handler.postDelayed(tick, 33);
        } else if (!allowed && CompassState.reading) {
            pause();
        }
        if (!enabled || !hasSlots) stopSelf();
        handler.removeCallbacks(retryWhenEligible);
        if (!CompassState.reading && enabled && hasSlots)
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
            Diagnostics.count("published");
        }
    }
    private void pause() {
        handler.removeCallbacks(tick);
        handler.removeCallbacks(retryWhenEligible);
        sensor.stop();
        awaitingFirstSample = false;
        motion.reset();
        CompassState.clear();
        hadFreshData = false;
        published = Float.NaN;
        CompassSource.requestUpdate(this);
        Diagnostics.event("sensorStop", 0);
    }
    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && "STOP".equals(intent.getAction())) CompassState.enable(this, false);
        refresh();
        return START_STICKY;
    }
    @Override public void onDisplayChanged(int id) {
        if (id == Display.DEFAULT_DISPLAY) { Diagnostics.event("displayCallback", id); refresh(); }
    }
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
