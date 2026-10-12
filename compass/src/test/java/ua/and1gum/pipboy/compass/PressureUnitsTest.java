package ua.and1gum.pipboy.compass;
import org.junit.Test;
import static org.junit.Assert.assertEquals;
public class PressureUnitsTest {
    @Test public void standardAtmosphereIs760Millimeters() {
        assertEquals("760", PressureUnits.millimeters(1013.25));
    }
    @Test public void localReadingRoundsToWholeMillimeters() {
        assertEquals("746", PressureUnits.millimeters(994));
        assertEquals("745", PressureUnits.millimeters(993));
    }
}
