package ua.and1gum.pipboy.compass;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import org.junit.Test;
import static org.junit.Assert.*;

public class SolarTimesCacheTest {
 private final ZonedDateTime day=ZonedDateTime.of(2026,6,21,12,0,0,0,ZoneId.of("Europe/Kyiv"));

 @Test public void bothSlotsAndLaterSameDayCalculateOnce(){
  int[] calls={0};
  SolarTimesCache cache=new SolarTimesCache((date,lat,lon)->{calls[0]++;return new String[]{"04:46","21:13"};});
  assertArrayEquals(new String[]{"04:46","21:13"},cache.forDay(day,50.45,30.52));
  assertArrayEquals(new String[]{"04:46","21:13"},cache.forDay(day.plusHours(10),50.45,30.52));
  assertEquals(1,calls[0]);
 }

 @Test public void dateZoneAndExactCoordinatesEachInvalidate(){
  int[] calls={0};
  SolarTimesCache cache=new SolarTimesCache((date,lat,lon)->{calls[0]++;return new String[]{"04:46","21:13"};});
  cache.forDay(day,50.45,30.52);
  cache.forDay(day.plusDays(1),50.45,30.52);
  cache.forDay(day.plusDays(1).withZoneSameLocal(ZoneId.of("Europe/Oslo")),50.45,30.52);
  cache.forDay(day.plusDays(1).withZoneSameLocal(ZoneId.of("Europe/Oslo")),Math.nextUp(50.45),30.52);
  cache.forDay(day.plusDays(1).withZoneSameLocal(ZoneId.of("Europe/Oslo")),Math.nextUp(50.45),Math.nextUp(30.52));
  assertEquals(5,calls[0]);
 }

 @Test public void onlyLatestResultIsRetained(){
  int[] calls={0};
  SolarTimesCache cache=new SolarTimesCache((date,lat,lon)->{calls[0]++;return new String[]{"04:46","21:13"};});
  cache.forDay(day,50.45,30.52);
  cache.forDay(day.plusDays(1),50.45,30.52);
  cache.forDay(day,50.45,30.52);
  assertEquals(3,calls[0]);
 }

 @Test public void unavailablePolarEventsAreCachedAndDefensivelyCopied(){
  int[] calls={0};String[] calculated={"—","—"};
  SolarTimesCache cache=new SolarTimesCache((date,lat,lon)->{calls[0]++;return calculated;});
  String[] first=cache.forDay(day,78.22,15.65);
  first[0]="changed";calculated[1]="changed";
  assertArrayEquals(new String[]{"—","—"},cache.forDay(day,78.22,15.65));
  assertEquals(1,calls[0]);
 }
}
