package com.sonata.app

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class SonataApplication : Application() {
    override fun onCreate() {
        super.onCreate()
    }
}