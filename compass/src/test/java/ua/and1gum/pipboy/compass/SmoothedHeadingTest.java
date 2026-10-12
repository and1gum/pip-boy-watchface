package ua.and1gum.pipboy.compass;
import org.junit.Test;
import static org.junit.Assert.*;
public class SmoothedHeadingTest {
    @Test public void northCrossingTakesShortPathBothWays() {
        SmoothedHeading f=new SmoothedHeading();
        assertEquals(359, f.update(359,1000),0.001);
        double forward=f.update(1,1100);
        assertTrue(forward>359 && forward<361);
        double back=f.update(358,1200);
        assertTrue(back<forward && back>358);
    }
    @Test public void filtersJitterWithoutFreezingAndResetDropsOldTurns() {
        SmoothedHeading f=new SmoothedHeading();
        f.update(90,1000);
        double filtered=f.update(100,1020);
        assertTrue(filtered>90 && filtered<95);
        assertTrue(f.update(100,2020)>99);
        f.reset();
        assertEquals(270,f.update(270,3000),0.001);
    }
}
