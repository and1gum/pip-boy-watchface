package ua.and1gum.pipboy.compass;
import org.junit.Test;
import java.util.List;
import static org.junit.Assert.*;
public class PressureHistoryTest {
 @Test public void missingHistoryIsNotStable(){assertEquals("?",PressureHistory.trend(List.of(),4*PressureHistory.HOUR,1013));}
 @Test public void trendUsesThreeHourBaseline(){
  var history=List.of(new PressureHistory.Sample(PressureHistory.HOUR,1013));
  assertEquals("up",PressureHistory.trend(history,4*PressureHistory.HOUR,1014));
  assertEquals("down",PressureHistory.trend(history,4*PressureHistory.HOUR,1012));
  assertEquals("steady",PressureHistory.trend(history,4*PressureHistory.HOUR,1013.8f));
  assertEquals("?",PressureHistory.trend(history,2*PressureHistory.HOUR,1013));
 }
 @Test public void persistenceFiltersCorruptionFutureAndStaleSamples(){
  assertEquals(1,PressureHistory.decode("0,1013;999999999,1012;10000000,NaN;10000000,1010;bad",15000000).size());
 }
}
