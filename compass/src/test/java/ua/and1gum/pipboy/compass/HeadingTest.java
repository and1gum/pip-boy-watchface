package ua.and1gum.pipboy.compass;

import static org.junit.Assert.*;
import org.junit.Test;
import java.util.Locale;

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
        assertThrows(IllegalArgumentException.class, () -> Heading.degrees(Double.NEGATIVE_INFINITY));
    }
    @Test public void everyIntegerLabelRetainsItsExactFormatAcrossTurnsAndLocales() {
        Locale previous = Locale.getDefault();
        try {
            Locale.setDefault(Locale.forLanguageTag("ar"));
            for (int degrees = 0; degrees < 360; degrees++) {
                String digits = degrees < 10 ? "00" + degrees : degrees < 100 ? "0" + degrees : "" + degrees;
                String direction = degrees < 23 ? "N" : degrees < 68 ? "NE" : degrees < 113 ? "E"
                        : degrees < 158 ? "SE" : degrees < 203 ? "S" : degrees < 248 ? "SW"
                        : degrees < 293 ? "W" : degrees < 338 ? "NW" : "N";
                String expected = direction + " · " + digits + "°";
                assertEquals(expected, Heading.label(degrees));
                assertEquals(expected, Heading.label(degrees - 720));
                assertEquals(expected, Heading.label(degrees + 720));
            }
        } finally {
            Locale.setDefault(previous);
        }
    }
    @Test public void repeatedEquivalentHeadingsReuseImmutableLabels() {
        for (int degrees = 0; degrees < 360; degrees++) {
            String label = Heading.label(degrees);
            assertSame(label, Heading.label(degrees));
            assertSame(label, Heading.label(degrees - 360));
            assertSame(label, Heading.label(degrees + 360));
        }
    }
}
