plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.arkadia.console"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.arkadia.console"
        minSdk = 29
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"
        buildConfigField("String", "FIREBASE_API_KEY", "\"" + (project.findProperty("firebaseApiKey") ?: System.getenv("FIREBASE_API_KEY") ?: "") + "\"")
        buildConfigField("String", "FIREBASE_PROJECT_ID", "\"" + (project.findProperty("firebaseProjectId") ?: System.getenv("FIREBASE_PROJECT_ID") ?: "") + "\"")
        buildConfigField("String", "FIREBASE_APP_ID", "\"" + (project.findProperty("firebaseAppId") ?: System.getenv("FIREBASE_APP_ID") ?: "") + "\"")
        buildConfigField("String", "FIREBASE_GCM_SENDER_ID", "\"" + (project.findProperty("firebaseGcmSenderId") ?: System.getenv("FIREBASE_GCM_SENDER_ID") ?: "") + "\"")
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            isDebuggable = true
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    buildFeatures { buildConfig = true }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-play-services:1.7.3")
    implementation(platform("com.google.firebase:firebase-bom:33.9.0"))
    implementation("com.google.firebase:firebase-auth")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    testImplementation("junit:junit:4.13.2")
}
