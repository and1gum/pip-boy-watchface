package ua.and1gum.pipboy.compass;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** User-controlled start/stop of the background provider; never holds screen awake. */
public final class CompassActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private TextView status;
    private Button toggle;
    private final Runnable update = new Runnable() {
        @Override public void run() {
            String value = CompassState.fresh() ? Heading.label(CompassState.heading)
                    : CompassState.reading ? "Waiting for compass…" : "Sensors paused";
            status.setText(value + "\n\nMagnetic north\n" +
                    (CompassState.hasSlots(CompassActivity.this) ? "Display sleep pauses sensors" : "Select Compass on your watch face"));
            toggle.setText(CompassState.enabled(CompassActivity.this) ? "Stop compass" : "Enable compass");
            handler.postDelayed(this, 500);
        }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(32, 40, 32, 40);
        layout.setBackgroundColor(Color.BLACK);
        status = new TextView(this);
        status.setGravity(Gravity.CENTER);
        status.setTextColor(Color.rgb(145, 248, 148));
        status.setTextSize(17);
        toggle = new Button(this);
        toggle.setOnClickListener(view -> {
            CompassState.enable(this, !CompassState.enabled(this));
            if (CompassState.enabled(this)) CompassTrackingService.start(this);
            else stopService(new android.content.Intent(this, CompassTrackingService.class));
            CompassSource.requestUpdate(this);
        });
        layout.addView(status);
        layout.addView(toggle);
        setContentView(layout);
        CompassTrackingService.start(this);
    }
    @Override public void onResume() { super.onResume(); handler.post(update); }
    @Override public void onPause() { handler.removeCallbacksAndMessages(null); super.onPause(); }
}
