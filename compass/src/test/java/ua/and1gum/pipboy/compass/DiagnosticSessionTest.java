package ua.and1gum.pipboy.compass;

import org.junit.Test;
import static org.junit.Assert.*;

public class DiagnosticSessionTest {
    @Test public void offSessionIgnoresEventsAndCounts() {
        DiagnosticSession s = new DiagnosticSession();
        s.event(5, "sample", 7);
        s.count(5, "sample");
        assertFalse(s.active(5));
        assertEquals("{\"recorded\":false}", s.json(5));
    }
    @Test public void newest1024EventsSurviveInChronologicalOrder() {
        DiagnosticSession s = started();
        for (int i = 0; i < 1030; i++) s.event(100 + i, "callback", i);
        String json = s.json(1130);
        assertTrue(json.contains("\"overwrittenEvents\":6"));
        assertFalse(json.contains("\"value\":5}"));
        assertTrue(json.contains("\"value\":6}"));
        assertTrue(json.indexOf("\"value\":6}") < json.indexOf("\"value\":1029}"));
        assertEquals(1024, occurrences(json, "\"name\":\"callback\""));
    }
    @Test public void countsAggregateWithoutConsumingEventCapacity() {
        DiagnosticSession s = started();
        for (int i = 0; i < 2500; i++) s.count(101, "samples");
        String json = s.json(102);
        assertTrue(json.contains("\"samples\":2500"));
        assertTrue(json.contains("\"events\":[]"));
    }
    @Test public void sessionExpiresAt15MinutesWithoutAddingNewRecords() {
        DiagnosticSession s = started();
        s.count(900099, "samples");
        s.event(900100, "tooLate", 1);
        s.count(900101, "samples");
        assertFalse(s.active(900101));
        String json = s.json(900102);
        assertTrue(json.contains("\"samples\":1"));
        assertTrue(json.contains("\"endedElapsedMs\":900100"));
        assertTrue(json.contains("\"endReason\":\"timeout\""));
        assertFalse(json.contains("tooLate"));
    }
    @Test public void stopRetainsDataAndNewStartReplacesIt() {
        DiagnosticSession s = started();
        s.event(110, "old", 5);
        s.stop(120);
        s.event(130, "ignored", 6);
        assertFalse(s.active(130));
        assertTrue(s.json(130).contains("\"name\":\"old\""));
        assertFalse(s.json(130).contains("ignored"));
        s.start(200, 300, "new");
        assertTrue(s.active(201));
        assertFalse(s.json(201).contains("\"name\":\"old\""));
    }
    @Test public void jsonEscapesMetadataAndNames() {
        DiagnosticSession s = new DiagnosticSession();
        s.start(1, 2, "v\"\\\n\t\u0001");
        s.event(2, "a\"\\\n", -7);
        String json = s.json(3);
        assertTrue(json.contains("\"build\":\"v\\\"\\\\\\n\\t\\u0001\""));
        assertTrue(json.contains("\"name\":\"a\\\"\\\\\\n\""));
        assertTrue(json.contains("\"value\":-7"));
    }
    @Test public void unboundedNamesAndMetadataCannotGrowExportWithoutLimit() {
        DiagnosticSession s = new DiagnosticSession();
        s.start(1, 2, "x".repeat(10000));
        for (int i = 0; i < 10000; i++) {
            s.event(2, "event" + i + "x".repeat(1000), i);
            s.count(2, "counter" + i);
        }
        String json = s.json(3);
        assertTrue(json.length() < 200000);
        assertTrue(json.contains("\"droppedNames\":"));
        assertFalse(json.contains("x".repeat(300)));
    }
    private DiagnosticSession started() {
        DiagnosticSession s = new DiagnosticSession();
        s.start(100, 1000, "0.2.0");
        return s;
    }
    private int occurrences(String text, String needle) {
        int count = 0, from = 0;
        while ((from = text.indexOf(needle, from)) >= 0) { count++; from += needle.length(); }
        return count;
    }
}
