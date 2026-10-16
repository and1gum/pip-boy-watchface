package ua.and1gum.pipboy.compass;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.os.RemoteException;
import androidx.wear.watchface.complications.data.*;
import androidx.wear.watchface.complications.datasource.ComplicationDataSourceService;
import androidx.wear.watchface.complications.datasource.ComplicationDataSourceUpdateRequester;
import androidx.wear.watchface.complications.datasource.ComplicationRequest;
import java.time.Instant;

/** Standard complication provider, refreshed by public push requests. */
public final class CompassSource extends ComplicationDataSourceService {
    private static volatile ComplicationDataSourceUpdateRequester requester;
    private int cachedDegrees = -1;
    private PlainComplicationText cachedLabel, cachedDescription, cachedShortText;
    static void requestUpdate(Context context) {
        ComplicationDataSourceUpdateRequester current = requester;
        if (current == null) {
            synchronized (CompassSource.class) {
                current = requester;
                if (current == null) requester = current = ComplicationDataSourceUpdateRequester.create(
                        context.getApplicationContext(), new ComponentName(context, CompassSource.class));
            }
        }
        Diagnostics.count("updateRequested");
        current.requestUpdateAll();
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
        Diagnostics.count("providerRequested");
        boolean fresh = CompassState.fresh();
        ComplicationData payload = fresh ? data(request.getComplicationType(), CompassState.heading, CompassState.continuousHeading, false)
                : new NoDataComplicationData();
        try {
            listener.onComplicationData(payload);
            Diagnostics.count(fresh ? "dataAccepted" : "noDataAccepted");
        } catch (RemoteException disconnected) {
            Diagnostics.event("providerDisconnected", 0);
        }
    }
    @Override public ComplicationData getPreviewData(ComplicationType type) { return data(type, 42, 42, true); }
    // Preview requests arrive on Binder threads while live requests run on main.
    private synchronized ComplicationData data(ComplicationType type, int degrees, float continuous, boolean preview) {
        if (cachedDegrees != degrees) {
            cachedDegrees = degrees;
            cachedLabel = new PlainComplicationText.Builder(Heading.label(degrees)).build();
            cachedDescription = new PlainComplicationText.Builder("Magnetic heading " + degrees + " degrees").build();
            cachedShortText = new PlainComplicationText.Builder(degrees + "°").build();
        }
        TimeRange validity = TimeRange.between(Instant.now(), Instant.now().plusSeconds(5));
        if (type == ComplicationType.RANGED_VALUE) {
            RangedValueComplicationData.Builder builder = new RangedValueComplicationData.Builder(continuous, Math.min(0, continuous), Math.max(360, continuous), cachedDescription)
                    .setText(cachedLabel);
            if (!preview) builder.setValidTimeRange(validity);
            return builder.build();
        }
        if (type == ComplicationType.SHORT_TEXT) {
            ShortTextComplicationData.Builder builder = new ShortTextComplicationData.Builder(
                    cachedShortText, cachedDescription);
            if (!preview) builder.setValidTimeRange(validity);
            return builder.build();
        }
        return new NoDataComplicationData();
    }
}
