package ua.and1gum.pipboy.compass;

import static org.junit.Assert.*;
import org.junit.Test;

public class HeadingTest {
    @Test public void wrapsAcrossNorthAndFormatsThreeDigits() {
        assertEquals(0, Heading.degrees(359.7));
        assertEquals(359, Heading.degrees(-1));
        assertEquals(42, Heading.degrees(402));
        assertEquals("NE · 042°", Heading.label(42));
        assertEquals("N · 000°", Heading.label(0));
        assertEquals("W · 270°", Heading.label(270));
    }
    @Test public void roundsCardinalBoundariesConsistently() {
        assertEquals("N · 022°", Heading.label(22));
        assertEquals("NE · 023°", Heading.label(23));
        assertEquals("N · 338°", Heading.label(338));
        assertEquals("NW · 337°", Heading.label(337));
    }
    @Test public void rejectsNonFiniteSensorValues() {
        assertThrows(IllegalArgumentException.class, () -> Heading.degrees(Double.NaN));
        assertThrows(IllegalArgumentException.class, () -> Heading.degrees(Double.POSITIVE_INFINITY));
    }
}
