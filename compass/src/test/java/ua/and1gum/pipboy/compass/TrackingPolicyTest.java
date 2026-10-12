package ua.and1gum.pipboy.compass;

import org.junit.Test;
import static org.junit.Assert.*;

public class TrackingPolicyTest {
    @Test public void stopsForEveryInactiveDisplayAndSessionState() {
        assertTrue(TrackingPolicy.shouldRead(true, true, true, true, true));
        assertFalse(TrackingPolicy.shouldRead(false, true, true, true, true));
        assertFalse(TrackingPolicy.shouldRead(true, false, true, true, true));
        assertFalse(TrackingPolicy.shouldRead(true, true, false, true, true));
        assertFalse(TrackingPolicy.shouldRead(true, true, true, false, true)); // AOD
        assertFalse(TrackingPolicy.shouldRead(true, true, true, true, false)); // locked
    }
    @Test public void publishesFirstFixAndChangesWithoutFloodingOrWraparoundSpikes() {
        assertTrue(TrackingPolicy.shouldPublish(Float.NaN, 0, 0, 10));
        assertFalse(TrackingPolicy.shouldPublish(90, 90, 1000, 2000));
        assertTrue(TrackingPolicy.shouldPublish(90, 90, 1000, 5000)); // refresh validity while still
        assertFalse(TrackingPolicy.shouldPublish(90, 100, 1000, 1032));
        assertTrue(TrackingPolicy.shouldPublish(359, 0, 1000, 1033));
        assertTrue(TrackingPolicy.shouldPublish(0, 359, 1000, 1033));
        assertTrue(TrackingPolicy.shouldPublish(-2, -1.9f, 1000, 1033));
        assertFalse(TrackingPolicy.shouldPublish(2, 2.01f, 1000, 1033));
    }
    @Test public void expiredAndUnreliableReadingsNeverBecomeNorth() {
        assertTrue(TrackingPolicy.isFresh(1000, 5999, 1));
        assertFalse(TrackingPolicy.isFresh(1000, 6000, 1));
        assertFalse(TrackingPolicy.isFresh(0, 1000, 3));
        assertFalse(TrackingPolicy.isFresh(1000, 1500, 0));
    }
}
