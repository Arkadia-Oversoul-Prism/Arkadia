package com.arkadia.os

import android.content.Context
import android.content.Intent
import android.os.Build
import android.speech.tts.TextToSpeech
import android.webkit.JavascriptInterface
import java.util.Locale

/**
 * Exposed to the Prism web app as `window.ArkadiaAndroid`.
 *
 * Usage in the frontend:
 *   if (window.ArkadiaAndroid) {
 *       window.ArkadiaAndroid.speakText("Hello from the vault")
 *       const url = window.ArkadiaAndroid.getArkadiaUrl()
 *   }
 */
class JavaScriptBridge(
    private val context: Context,
    private val prefs: Prefs,
    private val onOpenSettings: () -> Unit,
) {

    private var tts: TextToSpeech? = null

    init {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.language = Locale.getDefault()
            }
        }
    }

    @JavascriptInterface
    fun isAndroid(): Boolean = true

    @JavascriptInterface
    fun getVersion(): String = "1.0.0"

    @JavascriptInterface
    fun getArkadiaUrl(): String = prefs.arkadiaUrl

    @JavascriptInterface
    fun getDeviceInfo(): String =
        """{"model":"${Build.MODEL}","sdk":${Build.VERSION.SDK_INT},"brand":"${Build.BRAND}"}"""

    @JavascriptInterface
    fun speakText(text: String) {
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "arkadia_tts")
    }

    @JavascriptInterface
    fun stopSpeaking() {
        tts?.stop()
    }

    @JavascriptInterface
    fun openSettings() {
        onOpenSettings()
    }

    @JavascriptInterface
    fun shareText(text: String, title: String = "Share from Arkadia") {
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, text)
            putExtra(Intent.EXTRA_TITLE, title)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(Intent.createChooser(intent, title).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        })
    }

    fun destroy() {
        tts?.shutdown()
        tts = null
    }
}
