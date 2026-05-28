package com.arkadia.sonata

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager

class SonataApp : Application() {
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Sonata Playback",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "ARKANA voice playback controls"
            setShowBadge(false)
        }
        getSystemService(NotificationManager::class.java)
            .createNotificationChannel(channel)
    }

    companion object {
        const val CHANNEL_ID = "sonata_playback"
        const val NOTIF_ID   = 1001
    }
}
