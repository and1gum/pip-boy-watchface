package ua.and1gum.pipboy.compass;
import org.junit.Test;
import java.time.*;
import static org.junit.Assert.*;
public class SolarTimesTest {
 @Test public void kyivSummerDayHasMorningRiseAndEveningSet(){
  String[] times=SolarTimes.forDay(ZonedDateTime.of(2026,6,21,12,0,0,0,ZoneId.of("Europe/Kyiv")),50.45,30.52);
  assertTrue(times[0].startsWith("04:"));assertTrue(times[1].startsWith("21:"));
 }
 @Test public void eveningStillReturnsTodaysMorning(){
  ZoneId zone=ZoneId.of("Europe/Kyiv");
  String[] morning=SolarTimes.forDay(ZonedDateTime.of(2026,10,12,8,0,0,0,zone),50.45,30.52);
  String[] evening=SolarTimes.forDay(ZonedDateTime.of(2026,10,12,23,0,0,0,zone),50.45,30.52);
  assertArrayEquals(morning,evening);
 }
 @Test public void polarDayDoesNotInventTimes(){
  String[] times=SolarTimes.forDay(ZonedDateTime.of(2026,6,21,12,0,0,0,ZoneId.of("Europe/Oslo")),78.22,15.65);
  assertArrayEquals(new String[]{"—","—"},times);
 }
}
