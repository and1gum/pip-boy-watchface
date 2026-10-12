package ua.and1gum.pipboy.compass;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
/** Recalculate the local calendar day when the system date or time zone changes. */
public final class SolarDateReceiver extends BroadcastReceiver {
 @Override public void onReceive(Context context,Intent intent){SolarSource.refresh(context);}
}
