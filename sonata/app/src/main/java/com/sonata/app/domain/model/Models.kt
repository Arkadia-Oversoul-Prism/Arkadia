package com.sonata.app.domain.model

data class Voice(
    val id: String,
    val name: String,
    val language: String,
    val gender: VoiceGender,
    val quality: VoiceQuality,
    val isDownloaded: Boolean = false,
    val modelPath: String? = null,
    val fileSize: Long = 0
)

enum class VoiceGender {
    MALE, FEMALE, NEUTRAL
}

enum class VoiceQuality {
    LOW, MEDIUM, HIGH
}

data class PlaybackState(
    val isPlaying: Boolean = false,
    val isPaused: Boolean = false,
    val currentText: String = "",
    val progress: Float = 0f,
    val speed: Float = 1.0f,
    val pitch: Float = 1.0f
)

data class AppSettings(
    val selectedVoiceId: String = "",
    val playbackSpeed: Float = 1.0f,
    val playbackPitch: Float = 1.0f,
    val autoReadEnabled: Boolean = true,
    val overlayOpacity: Float = 0.95f,
    val darkModeEnabled: Boolean = true
)