package com.arkadia.os

import android.content.Context
import android.content.SharedPreferences

class Prefs(context: Context) {

    private val sp: SharedPreferences =
        context.applicationContext.getSharedPreferences("arkadia_prefs", Context.MODE_PRIVATE)

    /**
     * The root URL of the deployed Arkadia instance.
     * Serves both the Prism frontend (/) and Oracle Temple API (/api/*).
     * e.g.  https://arkadia-xxxx.replit.app
     *       http://10.0.2.2:5000  (emulator → host dev server)
     */
    var arkadiaUrl: String
        get()  = sp.getString(KEY_URL, "") ?: ""
        set(v) = sp.edit().putString(KEY_URL, v.trimEnd('/')).apply()

    /** Show address bar in the WebView */
    var showAddressBar: Boolean
        get()  = sp.getBoolean(KEY_ADDRESS_BAR, false)
        set(v) = sp.edit().putBoolean(KEY_ADDRESS_BAR, v).apply()

    companion object {
        private const val KEY_URL         = "arkadia_url"
        private const val KEY_ADDRESS_BAR = "show_address_bar"

        /** Emulator shortcut — points at the host machine's dev server */
        const val DEFAULT_URL = "http://10.0.2.2:5000"
    }
}
