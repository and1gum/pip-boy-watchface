package ua.and1gum.pipboy.compass;

import java.time.ZonedDateTime;
import java.time.LocalDate;
import java.time.ZoneId;

/** One solar-day result shared by callers. */
final class SolarTimesCache {
 interface Calculator { String[] calculate(ZonedDateTime date,double lat,double lon); }
 private record Key(LocalDate date,ZoneId zone,long lat,long lon) {}
 private final Calculator calculator;
 private Key key;
 private String[] value;
 SolarTimesCache(Calculator calculator){this.calculator=calculator;}
 synchronized String[] forDay(ZonedDateTime date,double lat,double lon){
  Key requested=new Key(date.toLocalDate(),date.getZone(),Double.doubleToLongBits(lat),Double.doubleToLongBits(lon));
  if(!requested.equals(key)){
   String[] calculated=calculator.calculate(date,lat,lon);
   value=calculated.clone();key=requested;
  }
  return value.clone();
 }
}
