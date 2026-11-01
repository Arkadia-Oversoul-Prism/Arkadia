package com.arkadia.webviewpoc

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OriginPolicyTest {
    private val origin = "https://arkadia-staging.example"

    @Test fun acceptsConfiguredHttpsOriginAndPaths() {
        assertTrue(OriginPolicy.isTrusted(origin, origin))
        assertTrue(OriginPolicy.isTrusted("$origin/login?next=%2F", origin))
    }

    @Test fun rejectsLookalikeHosts() {
        assertFalse(OriginPolicy.isTrusted("https://arkadia-staging.example.attacker.test", origin))
        assertFalse(OriginPolicy.isTrusted("https://attacker.test", origin))
    }

    @Test fun rejectsCleartextAndDowngrade() {
        assertFalse(OriginPolicy.isTrusted("http://arkadia-staging.example", origin))
        assertFalse(OriginPolicy.isTrusted(origin, "http://arkadia-staging.example"))
    }

    @Test fun rejectsAlternatePortsAndUserInfo() {
        assertFalse(OriginPolicy.isTrusted("https://arkadia-staging.example:8443", origin))
        assertFalse(OriginPolicy.isTrusted("https://user@arkadia-staging.example", origin))
    }

    @Test fun rejectsMalformedAndNonWebSchemes() {
        assertFalse(OriginPolicy.isTrusted("javascript:alert(1)", origin))
        assertFalse(OriginPolicy.isTrusted("intent://anything", origin))
        assertFalse(OriginPolicy.isTrusted("not a url", origin))
    }
}
