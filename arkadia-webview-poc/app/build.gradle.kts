plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val configuredOrigin = providers.gradleProperty("arkadiaOrigin")
    .orElse("https://arkadia-poc.invalid")
    .get()
    .trim()
    .trimEnd('/')

android {
    namespace = "com.arkadia.webviewpoc"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.arkadia.webviewpoc"
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"
        buildConfigField("String", "ARKADIA_ORIGIN", "\"$configuredOrigin\"")
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures { buildConfig = true }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}
