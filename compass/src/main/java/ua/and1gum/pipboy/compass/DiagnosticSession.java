package ua.and1gum.pipboy.compass;

/** Bounded in-memory diagnostic recording; all times supplied by its caller. */
final class DiagnosticSession {
    private static final int CAPACITY = 1024;
    private static final int NAME_CAPACITY = 128;
    private static final long LIMIT_MS = 15 * 60 * 1000;
    private volatile boolean recording;
    private String[] names;
    private long[] counts, times, values;
    private int[] eventNames;
    private int nameCount, size, next;
    private long overwritten, droppedNames, started, utc, ended;
    private String build, endReason;

    synchronized void start(long elapsed, long utc, String build) {
        names = new String[NAME_CAPACITY];
        counts = new long[NAME_CAPACITY];
        times = new long[CAPACITY];
        values = new long[CAPACITY];
        eventNames = new int[CAPACITY];
        nameCount = size = next = 0;
        overwritten = droppedNames = ended = 0;
        started = elapsed;
        this.utc = utc;
        this.build = bounded(build, 256);
        endReason = "";
        recording = true;
    }
    boolean isRecording() { return recording; }
    synchronized boolean active(long now) {
        if (recording && now - started >= LIMIT_MS) {
            ended = started + LIMIT_MS;
            endReason = "timeout";
            recording = false;
        }
        return recording;
    }
    synchronized void stop(long now) {
        if (active(now)) {
            ended = now;
            endReason = "manual";
            recording = false;
        }
    }
    synchronized void event(long now, String name, long value) {
        if (!active(now)) return;
        int id = nameId(name);
        if (id < 0) return;
        eventNames[next] = id;
        times[next] = now;
        values[next] = value;
        next = (next + 1) % CAPACITY;
        if (size < CAPACITY) size++;
        else overwritten++;
    }
    synchronized void count(long now, String name) {
        if (!active(now)) return;
        int id = nameId(name);
        if (id >= 0 && counts[id] < Long.MAX_VALUE) counts[id]++;
    }
    private int nameId(String name) {
        String key = bounded(name, 64);
        for (int i = 0; i < nameCount; i++) if (names[i].equals(key)) return i;
        if (nameCount == NAME_CAPACITY) { droppedNames++; return -1; }
        names[nameCount] = key;
        return nameCount++;
    }
    synchronized String json(long now) {
        active(now);
        if (names == null) return "{\"recorded\":false}";
        StringBuilder out = new StringBuilder(65536);
        out.append("{\"recorded\":true,\"schema\":1,\"build\":");
        quote(out, build);
        out.append(",\"startedElapsedMs\":").append(started)
                .append(",\"startedUtcMs\":").append(utc)
                .append(",\"active\":").append(recording)
                .append(",\"endedElapsedMs\":").append(ended)
                .append(",\"endReason\":");
        quote(out, endReason);
        out.append(",\"overwrittenEvents\":").append(overwritten)
                .append(",\"droppedNames\":").append(droppedNames)
                .append(",\"counters\":{");
        boolean comma = false;
        for (int i = 0; i < nameCount; i++) {
            if (counts[i] == 0) continue;
            if (comma) out.append(',');
            quote(out, names[i]); out.append(':').append(counts[i]);
            comma = true;
        }
        out.append("},\"events\":[");
        int oldest = (next + CAPACITY - size) % CAPACITY;
        for (int i = 0; i < size; i++) {
            int index = (oldest + i) % CAPACITY;
            if (i != 0) out.append(',');
            out.append("{\"elapsedMs\":").append(times[index]).append(",\"name\":");
            quote(out, names[eventNames[index]]);
            out.append(",\"value\":").append(values[index]).append('}');
        }
        return out.append("]}").toString();
    }
    private static String bounded(String text, int limit) {
        if (text == null) return "";
        return text.length() <= limit ? text : text.substring(0, limit);
    }
    private static void quote(StringBuilder out, String text) {
        out.append('"');
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            switch (c) {
                case '"': out.append("\\\""); break;
                case '\\': out.append("\\\\"); break;
                case '\n': out.append("\\n"); break;
                case '\r': out.append("\\r"); break;
                case '\t': out.append("\\t"); break;
                default:
                    // Escape controls and UTF-16 surrogates, including truncated pairs.
                    if (c < 32 || Character.isSurrogate(c)) {
                        out.append("\\u");
                        for (int shift = 12; shift >= 0; shift -= 4)
                            out.append("0123456789abcdef".charAt((c >> shift) & 15));
                    } else out.append(c);
            }
        }
        out.append('"');
    }
}
