package ua.and1gum.pipboy.compass;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.RemoteException;
import android.util.Log;
import androidx.wear.watchface.complications.data.*;
import androidx.wear.watchface.complications.datasource.ComplicationDataSourceService;
import androidx.wear.watchface.complications.datasource.ComplicationDataSourceUpdateRequester;
import androidx.wear.watchface.complications.datasource.ComplicationRequest;
import java.time.Instant;

/** Standard complication provider, refreshed by public push requests. */
public final class CompassSource extends ComplicationDataSourceService {
    static void requestUpdate(Context context) {
        ComplicationDataSourceUpdateRequester.create(context,
                new ComponentName(context, CompassSource.class)).requestUpdateAll();
    }
    @Override public void onComplicationActivated(int id, ComplicationType type) {
        CompassState.slot(this, id, true);
        CompassTrackingService.start(this);
    }
    @Override public void onComplicationDeactivated(int id) {
        CompassState.slot(this, id, false);
        if (!CompassState.hasSlots(this)) stopService(new Intent(this, CompassTrackingService.class));
    }
    @Override public void onComplicationRequest(ComplicationRequest request, ComplicationRequestListener listener) {
        CompassState.slot(this, request.getComplicationInstanceId(), true);
        // Initial startup is attempted on activation or explicitly from the Activity;
        // never restart tracking in response to our own NoData push while asleep.
        ComplicationData payload = CompassState.fresh() ? data(request.getComplicationType(), CompassState.heading, CompassState.continuousHeading, false)
                : new NoDataComplicationData();
        try { listener.onComplicationData(payload); }
        catch (RemoteException disconnected) { Log.d("PipBoyCompass", "Watch face disconnected", disconnected); }
        Log.d("PipBoyCompass", "Delivered " + (CompassState.fresh() ? CompassState.heading : "NoData"));
    }
    @Override public ComplicationData getPreviewData(ComplicationType type) { return data(type, 42, 42, true); }
    private ComplicationData data(ComplicationType type, int degrees, float continuous, boolean preview) {
        PlainComplicationText label = new PlainComplicationText.Builder(Heading.label(degrees)).build();
        PlainComplicationText description = new PlainComplicationText.Builder("Magnetic heading " + degrees + " degrees").build();
        TimeRange validity = TimeRange.between(Instant.now(), Instant.now().plusSeconds(5));
        if (type == ComplicationType.RANGED_VALUE) {
            RangedValueComplicationData.Builder builder = new RangedValueComplicationData.Builder(continuous, Math.min(0, continuous), Math.max(360, continuous), description)
                    .setText(label);
            if (!preview) builder.setValidTimeRange(validity);
            return builder.build();
        }
        if (type == ComplicationType.SHORT_TEXT) {
            ShortTextComplicationData.Builder builder = new ShortTextComplicationData.Builder(
                    new PlainComplicationText.Builder(degrees + "°").build(), description);
            if (!preview) builder.setValidTimeRange(validity);
            return builder.build();
        }
        return new NoDataComplicationData();
    }
}
