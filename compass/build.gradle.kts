plugins { id("com.android.application") }
android {
    namespace = "ua.and1gum.pipboy.compass"
    compileSdk = 36
    defaultConfig {
        applicationId = "ua.and1gum.pipboy.compass"
        minSdk = 35
        targetSdk = 36
        versionCode = providers.gradleProperty("pipboyVersionCode").get().toInt()
        versionName = providers.gradleProperty("pipboyVersionName").get()
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildTypes {
        getByName("release") {
            isDebuggable = false
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    lint { abortOnError = true }
}
dependencies {
    implementation("org.shredzone.commons:commons-suncalc:3.11")
    implementation("androidx.wear.watchface:watchface-complications-data-source:1.2.1")
    testImplementation("junit:junit:4.13.2")
}
