plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "com.arkadia.os"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.arkadia.os"
        minSdk = 29
        targetSdk = 34
        versionCode = 2
        versionName = "1.0.1"
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
    implementation(libs.androidx.cardview)
}


// Package the exact Prism frontend into the APK during CI/builds. The Android shell
// therefore does not need a live frontend deployment to render the Lab.
tasks.register<Exec>("bundlePrismFrontend") {
    workingDir(rootProject.projectDir.parentFile.resolve("web/public_prism"))
    commandLine("bash", "-lc", "corepack enable && pnpm install --frozen-lockfile && VITE_ANDROID_BUNDLE=1 pnpm build && rm -rf ../../arkadia-android/app/src/main/assets/prism && mkdir -p ../../arkadia-android/app/src/main/assets/prism && cp -R dist/. ../../arkadia-android/app/src/main/assets/prism/")
}

tasks.named("preBuild") {
    dependsOn("bundlePrismFrontend")
}

// The build produces the bundled Prism assets above.
// Keep the Android project self-contained at package time without introducing a
// second frontend implementation.
