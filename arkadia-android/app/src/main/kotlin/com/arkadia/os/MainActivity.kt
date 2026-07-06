package com.arkadia.os

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.webkit.*
import androidx.appcompat.app.AppCompatActivity
import com.arkadia.os.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var prefs: Prefs
    private lateinit var bridge: JavaScriptBridge

    companion object {
        const val EXTRA_PROCESS_TEXT = "extra_process_text"
    }

    // ── Lifecycle ────────────────────────────────────────────────────────────

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs   = Prefs(this)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        bridge = JavaScriptBridge(
            context        = applicationContext,
            prefs          = prefs,
            onOpenSettings = { startActivity(Intent(this, SettingsActivity::class.java)) },
        )

        setupWebView()
        setupButtons()
        handleIncomingIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIncomingIntent(intent)
    }

    override fun onDestroy() {
        bridge.destroy()
        binding.webView.destroy()
        super.onDestroy()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (binding.webView.canGoBack()) binding.webView.goBack()
        else super.onBackPressed()
    }

    // ── WebView setup ────────────────────────────────────────────────────────

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        binding.webView.settings.apply {
            javaScriptEnabled      = true
            domStorageEnabled      = true
            databaseEnabled        = true
            allowFileAccess        = true
            mixedContentMode       = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode              = WebSettings.LOAD_DEFAULT
            userAgentString        = "${userAgentString} ArkadiaOS/1.0"
            setSupportZoom(false)
            builtInZoomControls    = false
        }

        binding.webView.addJavascriptInterface(bridge, "ArkadiaAndroid")
        binding.webView.setBackgroundColor(Color.parseColor("#0A0A0F"))

        binding.webView.webViewClient = object : WebViewClient() {

            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                binding.progressBar.visibility = View.VISIBLE
                binding.errorLayout.visibility = View.GONE
                binding.fabSettings.visibility = View.GONE
            }

            override fun onPageFinished(view: WebView, url: String) {
                binding.progressBar.visibility = View.GONE
                binding.fabSettings.visibility = View.VISIBLE
                injectPendingText()
            }

            override fun onReceivedError(
                view: WebView, request: WebResourceRequest, error: WebResourceError,
            ) {
                if (request.isForMainFrame) {
                    showError(error.description?.toString() ?: "Connection failed")
                }
            }

            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                val base = prefs.arkadiaUrl.ifBlank { Prefs.DEFAULT_URL }
                return if (url.startsWith("http") && !url.startsWith(base)) {
                    startActivity(Intent(Intent.ACTION_VIEW, android.net.Uri.parse(url)))
                    true
                } else false
            }
        }

        binding.webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView, newProgress: Int) {
                binding.progressBar.progress = newProgress
            }
        }

        loadArkadia()
    }

    private fun setupButtons() {
        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        binding.btnReload.setOnClickListener {
            loadArkadia()
        }
        binding.fabSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
    }

    // ── Navigation ───────────────────────────────────────────────────────────

    private fun loadArkadia() {
        val url = prefs.arkadiaUrl.ifBlank { Prefs.DEFAULT_URL }
        binding.errorLayout.visibility = View.GONE
        binding.webView.loadUrl(url)
    }

    private fun showError(message: String) {
        binding.progressBar.visibility = View.GONE
        binding.fabSettings.visibility = View.GONE
        binding.errorLayout.visibility = View.VISIBLE
        val url = prefs.arkadiaUrl.ifBlank { Prefs.DEFAULT_URL }
        binding.tvError.text = "$message\n\n$url"
    }

    // ── Process-text deep-link ───────────────────────────────────────────────

    private var pendingText: String? = null

    private fun handleIncomingIntent(intent: Intent?) {
        intent ?: return
        val text = (intent.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)
            ?: intent.getCharSequenceExtra(EXTRA_PROCESS_TEXT))
            ?.toString()?.trim()
        if (!text.isNullOrBlank()) pendingText = text
    }

    private fun injectPendingText() {
        val text = pendingText ?: return
        pendingText = null

        val escaped = text
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "")

        binding.webView.evaluateJavascript("""
            (function(){
              window.dispatchEvent(new CustomEvent('arkadia-process-text',{detail:{text:'$escaped'}}));
            })();
        """.trimIndent(), null)
    }
}
