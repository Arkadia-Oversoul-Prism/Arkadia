package com.arkadia.webviewpoc

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.webkit.CookieManager
import android.webkit.SslErrorHandler
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceError
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var offlinePanel: LinearLayout
    private lateinit var connectivity: ConnectivityManager
    private var networkCallback: ConnectivityManager.NetworkCallback? = null
    private val origin = BuildConfig.ARKADIA_ORIGIN.trimEnd('/')

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (!OriginPolicy.isTrusted(origin, origin)) {
            showConfigurationError("Build origin must be a valid HTTPS origin.")
            return
        }
        connectivity = getSystemService(ConnectivityManager::class.java)
        buildContent()
        configureWebView()
        if (savedInstanceState == null) {
            if (hasNetwork()) webView.loadUrl(origin) else showOffline()
        } else {
            val restored = webView.restoreState(savedInstanceState)
            if (restored == null && hasNetwork()) webView.loadUrl(origin)
        }
        registerNetworkCallback()
    }

    private fun buildContent() {
        val root = FrameLayout(this)
        webView = WebView(this)
        root.addView(webView, FrameLayout.LayoutParams(-1, -1))

        offlinePanel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(40, 40, 40, 40)
            setBackgroundColor(Color.rgb(10, 14, 22))
            visibility = View.GONE
        }
        offlinePanel.addView(TextView(this).apply {
            text = "ARKADIA IS OFFLINE"
            textSize = 20f
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
        })
        offlinePanel.addView(TextView(this).apply {
            text = "No action has been submitted. Reconnect and retry when the network is available."
            textSize = 14f
            setTextColor(Color.LTGRAY)
            gravity = Gravity.CENTER
            setPadding(0, 18, 0, 24)
        })
        offlinePanel.addView(Button(this).apply {
            text = "RETRY"
            setOnClickListener { if (hasNetwork()) webView.reload() else showOffline() }
        })
        root.addView(offlinePanel, FrameLayout.LayoutParams(-1, -1))
        setContentView(root)
    }

    @Suppress("SetJavaScriptEnabled")
    private fun configureWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            allowFileAccessFromFileURLs = false
            allowUniversalAccessFromFileURLs = false
            setSupportMultipleWindows(false)
            javaScriptCanOpenWindowsAutomatically = false
            mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW
            safeBrowsingEnabled = true
            loadsImagesAutomatically = true
            databaseEnabled = false
        }
        CookieManager.getInstance().apply {
            setAcceptCookie(true)
            setAcceptThirdPartyCookies(webView, false)
        }
        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val target = request.url.toString()
                if (OriginPolicy.isTrusted(target, origin)) return false
                openExternalIfSafe(request.url)
                return true
            }

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                if (OriginPolicy.isTrusted(url, origin)) offlinePanel.visibility = View.GONE
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: WebResourceError
            ) {
                super.onReceivedError(view, request, error)
                if (request.isForMainFrame) showOffline()
            }

            override fun onReceivedHttpError(
                view: WebView,
                request: WebResourceRequest,
                errorResponse: android.webkit.WebResourceResponse
            ) {
                super.onReceivedHttpError(view, request, errorResponse)
                if (request.isForMainFrame && errorResponse.statusCode >= 500) showOffline()
            }

            override fun onReceivedSslError(view: WebView, handler: SslErrorHandler, error: android.net.http.SslError) {
                handler.cancel()
                showConfigurationError("Secure connection could not be verified. Navigation was cancelled.")
            }
        }
    }

    private fun openExternalIfSafe(uri: Uri) {
        if (uri.scheme !in setOf("https", "http")) return
        runCatching { startActivity(Intent(Intent.ACTION_VIEW, uri)) }
            .onFailure { Toast.makeText(this, "External link could not be opened.", Toast.LENGTH_SHORT).show() }
    }

    private fun hasNetwork(): Boolean {
        val network = connectivity.activeNetwork ?: return false
        val caps = connectivity.getNetworkCapabilities(network) ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    private fun registerNetworkCallback() {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                runOnUiThread {
                    if (offlinePanel.visibility == View.VISIBLE) {
                        offlinePanel.visibility = View.GONE
                        webView.reload()
                    }
                }
            }
            override fun onLost(network: Network) {
                runOnUiThread {
                    if (!hasNetwork()) showOffline()
                }
            }
        }
        networkCallback = callback
        runCatching { connectivity.registerDefaultNetworkCallback(callback) }
    }

    private fun showOffline() {
        offlinePanel.visibility = View.VISIBLE
    }

    private fun showConfigurationError(message: String) {
        val text = TextView(this).apply {
            this.text = message
            textSize = 16f
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.rgb(10, 14, 22))
            gravity = Gravity.CENTER
            setPadding(32, 32, 32, 32)
        }
        setContentView(text)
    }

    override fun onSaveInstanceState(outState: Bundle) {
        if (::webView.isInitialized) webView.saveState(outState)
        super.onSaveInstanceState(outState)
    }

    @Deprecated("Deprecated in Android API 33; retained for compatibility with the POC minimum SDK.")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        networkCallback?.let { runCatching { connectivity.unregisterNetworkCallback(it) } }
        if (::webView.isInitialized) {
            (webView.parent as? android.view.ViewGroup)?.removeView(webView)
            webView.stopLoading()
            webView.webChromeClient = null
            webView.webViewClient = WebViewClient()
            webView.destroy()
        }
        super.onDestroy()
    }
}
