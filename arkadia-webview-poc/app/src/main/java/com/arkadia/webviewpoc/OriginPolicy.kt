package com.arkadia.webviewpoc

import java.net.URI

/**
 * Main-frame navigation is trusted only for the exact configured HTTPS origin.
 * No wildcard subdomains, cleartext HTTP, user-info, or non-default ports.
 */
object OriginPolicy {
    fun isTrusted(candidate: String, configuredOrigin: String): Boolean {
        return runCatching {
            val expected = URI(configuredOrigin)
            val actual = URI(candidate)
            expected.scheme.equals("https", ignoreCase = true) &&
                actual.scheme.equals("https", ignoreCase = true) &&
                expected.host != null &&
                expected.host.equals(actual.host, ignoreCase = true) &&
                effectivePort(expected) == effectivePort(actual) &&
                actual.userInfo == null
        }.getOrDefault(false)
    }

    private fun effectivePort(uri: URI): Int =
        if (uri.port == -1) 443 else uri.port
}
