package com.sonata.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.sonata.app.domain.model.AppSettings
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "sonata_settings")

@Singleton
class SettingsDataStore @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private object Keys {
        val SELECTED_VOICE_ID = stringPreferencesKey("selected_voice_id")
        val PLAYBACK_SPEED = floatPreferencesKey("playback_speed")
        val PLAYBACK_PITCH = floatPreferencesKey("playback_pitch")
        val AUTO_READ_ENABLED = booleanPreferencesKey("auto_read_enabled")
        val OVERLAY_OPACITY = floatPreferencesKey("overlay_opacity")
        val DARK_MODE_ENABLED = booleanPreferencesKey("dark_mode_enabled")
        val VOICES_DOWNLOADED = stringPreferencesKey("voices_downloaded")
    }

    val settings: Flow<AppSettings> = context.dataStore.data.map { prefs ->
        AppSettings(
            selectedVoiceId = prefs[Keys.SELECTED_VOICE_ID] ?: "",
            playbackSpeed = prefs[Keys.PLAYBACK_SPEED] ?: 1.0f,
            playbackPitch = prefs[Keys.PLAYBACK_PITCH] ?: 1.0f,
            autoReadEnabled = prefs[Keys.AUTO_READ_ENABLED] ?: true,
            overlayOpacity = prefs[Keys.OVERLAY_OPACITY] ?: 0.95f,
            darkModeEnabled = prefs[Keys.DARK_MODE_ENABLED] ?: true
        )
    }

    val downloadedVoices: Flow<Set<String>> = context.dataStore.data.map { prefs ->
        prefs[Keys.VOICES_DOWNLOADED]?.split(",")?.toSet() ?: emptySet()
    }

    suspend fun updateSelectedVoice(voiceId: String) {
        context.dataStore.edit { prefs ->
            prefs[Keys.SELECTED_VOICE_ID] = voiceId
        }
    }

    suspend fun updatePlaybackSpeed(speed: Float) {
        context.dataStore.edit { prefs ->
            prefs[Keys.PLAYBACK_SPEED] = speed
        }
    }

    suspend fun updatePlaybackPitch(pitch: Float) {
        context.dataStore.edit { prefs ->
            prefs[Keys.PLAYBACK_PITCH] = pitch
        }
    }

    suspend fun updateAutoRead(enabled: Boolean) {
        context.dataStore.edit { prefs ->
            prefs[Keys.AUTO_READ_ENABLED] = enabled
        }
    }

    suspend fun updateOverlayOpacity(opacity: Float) {
        context.dataStore.edit { prefs ->
            prefs[Keys.OVERLAY_OPACITY] = opacity
        }
    }

    suspend fun addDownloadedVoice(voiceId: String) {
        context.dataStore.edit { prefs ->
            val current = prefs[Keys.VOICES_DOWNLOADED]?.split(",")?.toSet() ?: emptySet()
            prefs[Keys.VOICES_DOWNLOADED] = (current + voiceId).joinToString(",")
        }
    }

    suspend fun removeDownloadedVoice(voiceId: String) {
        context.dataStore.edit { prefs ->
            val current = prefs[Keys.VOICES_DOWNLOADED]?.split(",")?.toSet() ?: emptySet()
            prefs[Keys.VOICES_DOWNLOADED] = (current - voiceId).joinToString(",")
        }
    }

    suspend fun clearCache() {
        context.dataStore.edit { prefs ->
            prefs[Keys.VOICES_DOWNLOADED] = ""
        }
    }
}