package ua.and1gum.pipboy.compass;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

/** Prevent Samsung Health from restoring its last screen instead of opening steps. */
public final class StepsLaunchActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            startActivity(new Intent().setComponent(new ComponentName(
                    "com.samsung.android.wear.shealth",
                    "com.samsung.android.wear.shealth.app.steps.view.StepsActivity"))
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP));
        } catch (ActivityNotFoundException unavailable) {
            Log.w("PipBoySteps", "Samsung Health steps screen unavailable", unavailable);
        }
        finish();
    }
}
