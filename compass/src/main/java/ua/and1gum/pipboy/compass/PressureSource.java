package ua.and1gum.pipboy.compass;

import android.content.SharedPreferences;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Handler;
import android.os.Looper;
import android.os.RemoteException;
import android.util.Log;
import androidx.wear.watchface.complications.data.*;
import androidx.wear.watchface.complications.datasource.*;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** One bounded sensor burst per requested update; no foreground service or wake lock. */
public final class PressureSource extends ComplicationDataSourceService {
    private final Handler handler=new Handler(Looper.getMainLooper());
    @Override public void onComplicationRequest(ComplicationRequest request, ComplicationRequestListener listener) {
        handler.post(()->{
            SensorManager manager=getSystemService(SensorManager.class);
            Sensor sensor=manager.getDefaultSensor(Sensor.TYPE_PRESSURE);
            if(sensor==null){ deliver(listener,new NoDataComplicationData()); return; }
            List<Float> readings=new ArrayList<>();
            SensorEventListener sampling=new SensorEventListener(){
                @Override public void onSensorChanged(SensorEvent event){
                    float p=event.values[0];
                    if(Float.isFinite(p) && p>=300 && p<=1100)readings.add(p);
                }
                @Override public void onAccuracyChanged(Sensor sensor,int accuracy){}
            };
            if(!manager.registerListener(sampling,sensor,SensorManager.SENSOR_DELAY_NORMAL,handler)){
                deliver(listener,new NoDataComplicationData());return;
            }
            handler.postDelayed(()->{
                manager.unregisterListener(sampling);
                if(readings.isEmpty()){deliver(listener,new NoDataComplicationData());return;}
                Collections.sort(readings);float p=readings.get(readings.size()/2);
                long now=System.currentTimeMillis();
                SharedPreferences prefs=getSharedPreferences("pressure",MODE_PRIVATE);
                List<PressureHistory.Sample> history=PressureHistory.decode(prefs.getString("history",""),now);
                String trend=PressureHistory.trend(history,now,p);
                prefs.edit().putString("history",PressureHistory.append(history,now,p)).apply();
                PlainComplicationText description=new PlainComplicationText.Builder("Local pressure "+PressureUnits.millimeters(p)+" millimeters of mercury; "+trend).build();
                ComplicationData data=new RangedValueComplicationData.Builder(p,300,1100,description)
                    .setText(new PlainComplicationText.Builder(PressureUnits.millimeters(p)).build())
                    .setTitle(new PlainComplicationText.Builder(trend).build())
                    .setValidTimeRange(TimeRange.between(Instant.now(),Instant.now().plusSeconds(900))).build();
                deliver(listener,data);Log.i("PipBoyPressure","Pressure="+p+" trend="+trend);
            },1500);
        });
    }
    private void deliver(ComplicationRequestListener listener,ComplicationData data){
        try{listener.onComplicationData(data);}catch(RemoteException disconnected){Log.d("PipBoyPressure","Face disconnected");}
    }
    @Override public ComplicationData getPreviewData(ComplicationType type){return new NoDataComplicationData();}
}
