package ua.and1gum.pipboy.compass;
import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.location.*;
import android.os.*;
import android.view.Gravity;
import android.widget.*;
import java.time.ZonedDateTime;
public final class EnvironmentActivity extends Activity {
 private TextView status;
 private CancellationSignal cancel;
 @Override public void onCreate(Bundle saved){
  super.onCreate(saved);
  LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);layout.setGravity(Gravity.CENTER);layout.setPadding(24,32,24,32);layout.setBackgroundColor(Color.BLACK);
  status=new TextView(this);status.setTextColor(Color.rgb(145,248,148));status.setGravity(Gravity.CENTER);status.setTextSize(18);layout.addView(status);
  Button update=new Button(this);update.setText("Оновити місце");update.setOnClickListener(v->locate());layout.addView(update);setContentView(layout);locate();
 }
 private void locate(){
  if(checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED){status.setText("Дозволь приблизне місце для сходу й заходу сонця");requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION},1);return;}
  show(SolarSource.latest(this));
  LocationManager manager=getSystemService(LocationManager.class);
  if(manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)){
   if(cancel!=null)cancel.cancel();cancel=new CancellationSignal();
   manager.getCurrentLocation(LocationManager.NETWORK_PROVIDER,cancel,getMainExecutor(),location->{if(location!=null)SolarSource.saveLocation(this,location);show(location!=null?location:SolarSource.latest(this));SolarSource.refresh(this);});
   new Handler(Looper.getMainLooper()).postDelayed(()->{if(cancel!=null)cancel.cancel();},20_000);
  }
  SolarSource.refresh(this);
 }
 private void show(Location location){
  if(location==null){status.setText("Очікуємо місце годинника…\nУвімкни місцезнаходження та онови");return;}
  String[] times=SolarTimes.forDay(ZonedDateTime.now(),location.getLatitude(),location.getLongitude());status.setText("Схід  "+times[0]+"\nЗахід  "+times[1]);
 }
 @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] grants){super.onRequestPermissionsResult(request,permissions,grants);if(grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED)locate();}
 @Override public void onDestroy(){if(cancel!=null)cancel.cancel();super.onDestroy();}
}
