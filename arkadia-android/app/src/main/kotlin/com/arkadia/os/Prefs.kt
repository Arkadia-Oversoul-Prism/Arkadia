package com.arkadia.os

import android.content.Context
import android.content.SharedPreferences
import java.util.UUID

class Prefs(context: Context) {
    private val sp: SharedPreferences = context.applicationContext.getSharedPreferences("arkadia_prefs", Context.MODE_PRIVATE)
    var arkadiaUrl: String
        get() = (sp.getString(KEY_URL, DEFAULT_URL) ?: DEFAULT_URL).ifBlank { DEFAULT_URL }
        set(v) = sp.edit().putString(KEY_URL, v.trimEnd('/')).apply()
    var apiUrl: String
        get() = sp.getString(KEY_API_URL, DEFAULT_API_URL) ?: DEFAULT_API_URL
        set(v) = sp.edit().putString(KEY_API_URL, v.trimEnd('/')).apply()
    var apiToken: String
        get() = sp.getString(KEY_TOKEN, "") ?: ""
        set(v) = sp.edit().putString(KEY_TOKEN, v.trim()).apply()
    val sessionId: String
        get() {
            val existing = sp.getString(KEY_SESSION, null)
            if (!existing.isNullOrBlank()) return existing
            val created = "android-" + UUID.randomUUID()
            sp.edit().putString(KEY_SESSION, created).apply()
            return created
        }
    companion object {
        private const val KEY_URL = "arkadia_url"
        private const val KEY_API_URL = "api_url"
        private const val KEY_TOKEN = "api_token"
        private const val KEY_SESSION = "session_id"
        const val DEFAULT_URL = "https://arkadia-prism.vercel.app"
        const val DEFAULT_API_URL = "https://arkadia-kw64.onrender.com"
    }
}
