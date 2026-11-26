plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "com.arkadia.sonata"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.arkadia.sonata"
        minSdk = 29
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            applicationIdSuffix = ".debug"
            isDebuggable = true
        }
    }

    buildFeatures {
        viewBinding = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.preference.ktx)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.okhttp)
    // MediaSessionCompat + MediaStyle notification
    implementation(libs.androidx.media)
    // CardView — used by overlay_player.xml
    implementation(libs.androidx.cardview)

    // Local JVM unit tests (src/test) — MieMusicalInterpreterTest resolves
    // org.junit.* from here.
    testImplementation(libs.junit)
    // `org.json` is an Android framework class: on the JVM unit-test classpath
    // it is a stub whose methods throw ("not mocked"), so a test that exercises
    // `MieMusicalObject.toJson()` cannot run without a real implementation.
    // `testDebugUnitTest` gates `assembleDebug`, so that failure suppressed the
    // APK build itself.
    testImplementation(libs.org.json)
}
