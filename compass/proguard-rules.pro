# WFF uses literal component names outside this module. Preserve their identity.
-keepnames class ua.and1gum.pipboy.compass.CompassSource
-keepnames class ua.and1gum.pipboy.compass.PressureSource
-keepnames class ua.and1gum.pipboy.compass.SolarSource
-keepnames class ua.and1gum.pipboy.compass.EnvironmentActivity
-keepnames class ua.and1gum.pipboy.compass.StepsLaunchActivity
# commons-suncalc marks static nullability with an optional SpotBugs annotation.
# No runtime code depends on the annotation class.
-dontwarn edu.umd.cs.findbugs.annotations.Nullable
