package com.arkadia.console

import android.content.Context
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseUser
import kotlinx.coroutines.tasks.await

class FirebaseIdentity private constructor(
    private val auth: FirebaseAuth
) {
    val currentUser: FirebaseUser? get() = auth.currentUser

    suspend fun idToken(forceRefresh: Boolean = false): String? =
        auth.currentUser?.getIdToken(forceRefresh)?.await()?.token

    suspend fun signIn(email: String, password: String): FirebaseUser =
        auth.signInWithEmailAndPassword(email.trim(), password).await().user
            ?: error("Firebase sign-in returned no user")

    suspend fun register(email: String, password: String): FirebaseUser =
        auth.createUserWithEmailAndPassword(email.trim(), password).await().user
            ?: error("Firebase registration returned no user")

    fun signOut() {
        auth.signOut()
    }

    companion object {
        fun initialize(context: Context): FirebaseIdentity? {
            val existing = FirebaseApp.getApps(context).firstOrNull()
            val app = existing ?: run {
                val apiKey = BuildConfig.FIREBASE_API_KEY
                val projectId = BuildConfig.FIREBASE_PROJECT_ID
                val appId = BuildConfig.FIREBASE_APP_ID
                if (apiKey.isBlank() || projectId.isBlank() || appId.isBlank()) return null
                FirebaseApp.initializeApp(
                    context,
                    FirebaseOptions.Builder()
                        .setApiKey(apiKey)
                        .setProjectId(projectId)
                        .setApplicationId(appId)
                        .apply {
                            BuildConfig.FIREBASE_GCM_SENDER_ID
                                .takeIf { it.isNotBlank() }
                                ?.let { setGcmSenderId(it) }
                        }
                        .build()
                )
            }
            return app?.let { FirebaseIdentity(FirebaseAuth.getInstance(it)) }
        }
    }
}
