plugins { id("com.android.application") }
android {
    namespace = "ua.and1gum.pipboy"
    compileSdk = 36
    defaultConfig {
        applicationId = "ua.and1gum.pipboy"
        minSdk = 35
        targetSdk = 36
        versionCode = 2
        versionName = "0.2.0"
    }
    lint { abortOnError = true }
}
