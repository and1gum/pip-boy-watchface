package ua.and1gum.pipboy.compass;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import org.shredzone.commons.suncalc.SunTimes;
final class SolarTimes {
 static String[] forDay(ZonedDateTime date,double lat,double lon){
  SunTimes times=SunTimes.compute().on(date.toLocalDate().atStartOfDay(date.getZone())).at(lat,lon).oneDay().execute();
  DateTimeFormatter fmt=DateTimeFormatter.ofPattern("HH:mm");
  return new String[]{times.getRise()==null?"—":fmt.format(times.getRise()),times.getSet()==null?"—":fmt.format(times.getSet())};
 }
}
