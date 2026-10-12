package ua.and1gum.pipboy.compass;
import org.junit.Test;
import static org.junit.Assert.*;
public class HeadingMotionTest {
 @Test public void retargetingPreservesPositionAndConverges() {
  HeadingMotion m=new HeadingMotion();
  m.target(10,1000); assertEquals(10,m.sample(1000),.0001);
  m.target(110,1100); assertEquals(10,m.sample(1100),.0001);
  double a=m.sample(1133), b=m.sample(1166);
  assertTrue(a>10 && b>a && b<110);
  m.target(-20,1166); assertEquals(b,m.sample(1166),.0001);
  assertTrue(m.sample(1199)<b);
  assertEquals(-20,m.sample(3000),.001);
 }
 @Test public void continuousNorthAndResetNeverCreateFullTurns() {
  HeadingMotion m=new HeadingMotion();
  m.target(359,1000); m.target(361,1100);
  assertTrue(m.sample(1133)>359 && m.sample(1133)<361);
  m.reset(); m.target(80,2000); assertEquals(80,m.sample(2000),.0001);
 }
}
