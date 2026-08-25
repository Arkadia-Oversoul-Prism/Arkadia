package com.arkadia.sonata

import android.content.Context
import android.content.SharedPreferences

/**
 * Thin SharedPreferences wrapper for Sonata TTS Reader.
 */
class Prefs(context: Context) {

    private val sp: SharedPreferences =
        context.applicationContext.getSharedPreferences("sonata_prefs", Context.MODE_PRIVATE)

    // ── ElevenLabs Settings ─────────────────────────────────────────────────

    /** Primary ElevenLabs API key */
    var elevenLabsKey1: String
        get() = sp.getString(KEY_EL_K1, "") ?: ""
        set(v) = sp.edit().putString(KEY_EL_K1, v).apply()

    /** Secondary ElevenLabs API key (backup) */
    var elevenLabsKey2: String
        get() = sp.getString(KEY_EL_K2, "") ?: ""
        set(v) = sp.edit().putString(KEY_EL_K2, v).apply()

    /** ElevenLabs voice ID */
    var elevenLabsVoice: String
        get() = sp.getString(KEY_EL_VOICE, "EXAVITQu4vr4xnSDxMaL") ?: "EXAVITQu4vr4xnSDxMaL" // Bella
        set(v) = sp.edit().putString(KEY_EL_VOICE, v).apply()

    // ── Speed & Controls ───────────────────────────────────────────────────

    /** 0.5 – 2.0 */
    var speed: Float
        get() = sp.getFloat(KEY_SPEED, 1.0f)
        set(v) = sp.edit().putFloat(KEY_SPEED, v).apply()

    // ── Legacy / Fallback ──────────────────────────────────────────────────

    /** Base URL of the Arkadia Oracle Temple backend (for Edge TTS fallback) */
    var edgeTtsUrl: String
        get() = sp.getString(KEY_EDGE_TTS_URL, "") ?: ""
        set(v) = sp.edit().putString(KEY_EDGE_TTS_URL, v).apply()

    /** Automatically start reading when text received via PROCESS_TEXT */
    var autoRead: Boolean
        get() = sp.getBoolean(KEY_AUTO_READ, true)
        set(v) = sp.edit().putBoolean(KEY_AUTO_READ, v).apply()

    /** Use ElevenLabs (true) or Android TTS (false) */
    var useElevenLabs: Boolean
        get() = sp.getBoolean(KEY_USE_EL, true)
        set(v) = sp.edit().putBoolean(KEY_USE_EL, v).apply()

    /** Prefer ElevenLabs when API key is configured */
    var preferElevenLabs: Boolean
        get() = sp.getBoolean(KEY_PREFER_EL, true)
        set(v) = sp.edit().putBoolean(KEY_PREFER_EL, v).apply()

    /** Returns the active ElevenLabs key or empty */
    fun getActiveElevenLabsKey(): String = elevenLabsKey1.ifBlank { elevenLabsKey2 }

    /** Returns true if ElevenLabs is configured */
    fun hasElevenLabsKey(): Boolean = elevenLabsKey1.isNotBlank() || elevenLabsKey2.isNotBlank()

    companion object {
        private const val KEY_EL_K1  = "el_key_1"
        private const val KEY_EL_K2  = "el_key_2"
        private const val KEY_EL_VOICE = "el_voice"
        private const val KEY_SPEED  = "speed"
        private const val KEY_EDGE_TTS_URL = "edge_tts_url"
        private const val KEY_AUTO_READ = "auto_read"
        private const val KEY_USE_EL  = "use_elevenlabs"
        private const val KEY_PREFER_EL = "prefer_elevenlabs"
    }
}
