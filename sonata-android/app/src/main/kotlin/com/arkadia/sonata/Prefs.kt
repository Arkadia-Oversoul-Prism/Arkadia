package com.arkadia.sonata

import android.content.Context
import android.content.SharedPreferences

/**
 * Thin SharedPreferences wrapper.
 * Keys are typed; all reads have safe defaults.
 */
class Prefs(context: Context) {

    private val sp: SharedPreferences =
        context.applicationContext.getSharedPreferences("sonata_prefs", Context.MODE_PRIVATE)

    var voice: String
        get() = sp.getString(KEY_VOICE, "aria") ?: "aria"
        set(v) = sp.edit().putString(KEY_VOICE, v).apply()

    /** 0.5 – 2.0 */
    var speed: Float
        get() = sp.getFloat(KEY_SPEED, 1.0f)
        set(v) = sp.edit().putFloat(KEY_SPEED, v).apply()

    /** 0.5 – 2.0  (Android TTS pitch; ignored for Edge TTS) */
    var pitch: Float
        get() = sp.getFloat(KEY_PITCH, 1.0f)
        set(v) = sp.edit().putFloat(KEY_PITCH, v).apply()

    /** Automatically start reading when text received via PROCESS_TEXT */
    var autoRead: Boolean
        get() = sp.getBoolean(KEY_AUTO_READ, true)
        set(v) = sp.edit().putBoolean(KEY_AUTO_READ, v).apply()

    var darkMode: Boolean
        get() = sp.getBoolean(KEY_DARK_MODE, true)
        set(v) = sp.edit().putBoolean(KEY_DARK_MODE, v).apply()

    /**
     * Base URL of the Arkadia Oracle Temple backend.
     * When set + device is online, the app calls /api/tts for neural audio.
     * Leave empty to always use offline Android TTS.
     */
    var edgeTtsUrl: String
        get() = sp.getString(KEY_EDGE_TTS_URL, "") ?: ""
        set(v) = sp.edit().putString(KEY_EDGE_TTS_URL, v).apply()

    /** Prefer Edge TTS (online) when URL is configured */
    var preferEdgeTts: Boolean
        get() = sp.getBoolean(KEY_PREFER_EDGE, true)
        set(v) = sp.edit().putBoolean(KEY_PREFER_EDGE, v).apply()

    companion object {
        private const val KEY_VOICE         = "voice"
        private const val KEY_SPEED         = "speed"
        private const val KEY_PITCH         = "pitch"
        private const val KEY_AUTO_READ     = "auto_read"
        private const val KEY_DARK_MODE     = "dark_mode"
        private const val KEY_EDGE_TTS_URL  = "edge_tts_url"
        private const val KEY_PREFER_EDGE   = "prefer_edge_tts"
    }
}
