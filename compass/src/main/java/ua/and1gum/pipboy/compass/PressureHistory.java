package ua.and1gum.pipboy.compass;

import java.util.ArrayList;
import java.util.List;

/** Sparse local pressure history. Unknown is distinct from stable. */
final class PressureHistory {
    record Sample(long time, float pressure) {}
    static final long HOUR = 3_600_000L;
    static String trend(List<Sample> samples, long now, float pressure) {
        Sample nearest = null;
        for (Sample sample : samples) {
            long age = now - sample.time();
            if (age >= 150*60_000L && age <= 210*60_000L &&
                    (nearest == null || Math.abs(age-3*HOUR) < Math.abs(now-nearest.time()-3*HOUR))) nearest=sample;
        }
        if (nearest == null) return "?";
        float delta=pressure-nearest.pressure();
        return delta >= 1f ? "up" : delta <= -1f ? "down" : "steady";
    }
    static List<Sample> decode(String encoded, long now) {
        List<Sample> result=new ArrayList<>();
        for (String row : encoded.split(";")) {
            try {
                String[] fields=row.split(",");
                long time=Long.parseLong(fields[0]); float p=Float.parseFloat(fields[1]);
                if (now>=time && now-time<=4*HOUR && Float.isFinite(p) && p>=300 && p<=1100) result.add(new Sample(time,p));
            } catch (RuntimeException malformed) { /* Ignore partial/corrupt entries. */ }
        }
        return result;
    }
    static String append(List<Sample> history,long now,float pressure) {
        if (history.isEmpty() || now-history.get(history.size()-1).time()>=5*60_000L) history.add(new Sample(now,pressure));
        StringBuilder out=new StringBuilder();
        for (Sample s:history) out.append(s.time()).append(',').append(s.pressure()).append(';');
        return out.toString();
    }
}
