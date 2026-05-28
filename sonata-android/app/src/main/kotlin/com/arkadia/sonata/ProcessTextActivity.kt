package com.arkadia.sonata

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast

/**
 * Handles android.intent.action.PROCESS_TEXT — appears as
 * "Speak with Sonata" in the native text-selection pop-up across all apps.
 *
 * No UI is shown (transparent theme). The activity starts SpeechService
 * (foreground) and optionally FloatingOverlayService, then finishes.
 * Target latency: < 300ms from tap to speech start.
 */
class ProcessTextActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val text = intent
            ?.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)
            ?.toString()
            ?.trim()

        if (text.isNullOrEmpty()) {
            finish(); return
        }

        val prefs = Prefs(this)

        // ── Start foreground TTS service ──────────────────────────────────
        val speechIntent = Intent(this, SpeechService::class.java).apply {
            action = SpeechService.ACTION_SPEAK
            putExtra(SpeechService.EXTRA_TEXT,  text)
            putExtra(SpeechService.EXTRA_LABEL, "SONATA")
        }
        startForegroundService(speechIntent)

        // ── Show floating overlay if permitted ────────────────────────────
        if (Settings.canDrawOverlays(this)) {
            val overlayIntent = Intent(this, FloatingOverlayService::class.java).apply {
                putExtra(FloatingOverlayService.EXTRA_LABEL,   "ORACLE TRANSMISSION")
                putExtra(FloatingOverlayService.EXTRA_PREVIEW, text)
            }
            startService(overlayIntent)
        } else {
            // Prompt for overlay permission (non-blocking)
            Toast.makeText(
                this,
                "Grant 'Display over other apps' in Settings for the floating player.",
                Toast.LENGTH_LONG
            ).show()
            requestOverlayPermission()
        }

        finish()
    }

    private fun requestOverlayPermission() {
        val intent = Intent(
            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
            Uri.parse("package:$packageName")
        )
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivity(intent)
    }
}
