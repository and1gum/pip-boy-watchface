plugins { id("com.android.application") }
android {
    namespace = "ua.and1gum.pipboy"
    compileSdk = 36
    defaultConfig {
        applicationId = "ua.and1gum.pipboy"
        minSdk = 35
        targetSdk = 36
        versionCode = providers.gradleProperty("pipboyVersionCode").get().toInt()
        versionName = providers.gradleProperty("pipboyVersionName").get()
    }
    // WFF resources are consumed by the system renderer, outside this APK's code graph.
    buildTypes { getByName("release") { isDebuggable = false; isShrinkResources = false } }
    lint { abortOnError = true }
}
