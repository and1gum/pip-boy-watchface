package ua.and1gum.pipboy.compass;
import android.Manifest;
import android.app.PendingIntent;
import android.content.*;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import android.os.RemoteException;
import android.os.CancellationSignal;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import java.util.concurrent.atomic.AtomicBoolean;
import android.util.Log;
import androidx.wear.watchface.complications.data.*;
import androidx.wear.watchface.complications.datasource.*;
import java.time.*;
public final class SolarSource extends ComplicationDataSourceService {
 static void refresh(Context c){ComplicationDataSourceUpdateRequester.create(c,new ComponentName(c,SolarSource.class)).requestUpdateAll();}
 static void saveLocation(Context c,Location location){
  c.getSharedPreferences("solar",0).edit().putLong("lat",Double.doubleToLongBits(location.getLatitude()))
   .putLong("lon",Double.doubleToLongBits(location.getLongitude()))
   .putLong("time",System.currentTimeMillis()-Math.max(0,SystemClock.elapsedRealtime()-location.getElapsedRealtimeNanos()/1_000_000L)).apply();
 }
 static Location latest(Context c){
  SharedPreferences prefs=c.getSharedPreferences("solar",0);
  Location best=null;
  if(prefs.contains("lat")){
   best=new Location("saved");best.setLatitude(Double.longBitsToDouble(prefs.getLong("lat",0)));
   best.setLongitude(Double.longBitsToDouble(prefs.getLong("lon",0)));best.setTime(prefs.getLong("time",0));
  }
  if(c.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED)return best;
  LocationManager m=c.getSystemService(LocationManager.class);
  Location live=null;
  for(String provider:new String[]{LocationManager.NETWORK_PROVIDER,"fused",LocationManager.PASSIVE_PROVIDER})try{
   if(!m.getAllProviders().contains(provider))continue;
   Location l=m.getLastKnownLocation(provider);
   if(l!=null && (live==null || l.getElapsedRealtimeNanos()>live.getElapsedRealtimeNanos()))live=l;
  }catch(SecurityException denied){Log.d("PipBoySolar","Using saved location");}
  if(live!=null){
   long age=Math.max(0,SystemClock.elapsedRealtime()-live.getElapsedRealtimeNanos()/1_000_000L);
   if(age<24*3600_000L){saveLocation(c,live);live.setTime(System.currentTimeMillis()-age);return live;}
  }
  return best;
 }
 @Override public void onComplicationRequest(ComplicationRequest request,ComplicationRequestListener listener){
  Location location=latest(this);
  long now=System.currentTimeMillis();
  SharedPreferences prefs=getSharedPreferences("solar",0);
  LocationManager manager=getSystemService(LocationManager.class);
  if(checkSelfPermission(Manifest.permission.ACCESS_BACKGROUND_LOCATION)==PackageManager.PERMISSION_GRANTED
    && checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED
    && (location==null || now-location.getTime()>30*60_000L)
    && now-prefs.getLong("attempt",0)>30*60_000L
    && manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)){
   prefs.edit().putLong("attempt",now).apply();
   CancellationSignal cancel=new CancellationSignal();AtomicBoolean done=new AtomicBoolean();
   Handler main=new Handler(Looper.getMainLooper());
   Runnable fallback=()->{if(done.compareAndSet(false,true)){cancel.cancel();deliver(listener,latest(this));}};
   main.postDelayed(fallback,10_000);
   try{
    manager.getCurrentLocation(LocationManager.NETWORK_PROVIDER,cancel,getMainExecutor(),fresh->{
     if(done.compareAndSet(false,true)){
      main.removeCallbacks(fallback);
      if(fresh!=null){saveLocation(this,fresh);Log.i("PipBoySolar","Approximate location refreshed automatically");}
      deliver(listener,fresh!=null?fresh:latest(this));
      if(fresh!=null)refresh(this);
     }
    });
   }catch(SecurityException denied){fallback.run();}
   return;
  }
  deliver(listener,location);
 }
 private void deliver(ComplicationRequestListener listener,Location location){
  ComplicationData payload=new NoDataComplicationData();
  if(location!=null){
   ZonedDateTime now=ZonedDateTime.now();String[] times=SolarTimes.forDay(now,location.getLatitude(),location.getLongitude());
   payload=new ShortTextComplicationData.Builder(new PlainComplicationText.Builder(times[0]).build(),new PlainComplicationText.Builder("Sunrise "+times[0]+" sunset "+times[1]).build())
    .setTitle(new PlainComplicationText.Builder(times[1]).build())
    .setTapAction(PendingIntent.getActivity(this,4,new Intent(this,EnvironmentActivity.class),PendingIntent.FLAG_IMMUTABLE))
    .setValidTimeRange(TimeRange.between(Instant.now(),now.toLocalDate().plusDays(1).atStartOfDay(now.getZone()).toInstant())).build();
   Log.i("PipBoySolar","Sunrise="+times[0]+" sunset="+times[1]);
  }
  try{listener.onComplicationData(payload);}catch(RemoteException disconnected){Log.d("PipBoySolar","Face disconnected");}
 }
 @Override public ComplicationData getPreviewData(ComplicationType type){return new NoDataComplicationData();}
}
