package com.arkadia.os

import android.app.Activity
import android.content.Intent
import android.os.Bundle

/**
 * Intercepts Android's PROCESS_TEXT intent (text selected in any app → Arkadia).
 * Passes the selected text to MainActivity which injects it into the Oracle via JS bridge.
 */
class ProcessTextActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val text = intent
            ?.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)
            ?.toString()
            ?.trim()

        if (!text.isNullOrBlank()) {
            val launch = Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
                putExtra(MainActivity.EXTRA_PROCESS_TEXT, text)
            }
            startActivity(launch)
        }

        finish()
    }
}
