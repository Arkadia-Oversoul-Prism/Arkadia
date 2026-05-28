package com.sonata.app.ui.screens

import android.app.Application
import android.content.Intent
import android.speech.tts.TextToSpeech
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.sonata.app.data.local.SettingsDataStore
import com.sonata.app.domain.model.Voice
import com.sonata.app.domain.model.VoiceGender
import com.sonata.app.domain.model.VoiceQuality
import com.sonata.app.service.TtsPlaybackService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class MainViewModel @Inject constructor(
    private val application: Application,
    private val settingsDataStore: SettingsDataStore
) : AndroidViewModel(application) {
    
    private var textToSpeech: TextToSpeech? = null
    private var isTtsReady = false
    
    private val _availableVoices = MutableStateFlow<List<Voice>>(getDefaultVoices())
    val availableVoices: StateFlow<List<Voice>> = _availableVoices.asStateFlow()
    
    private val _selectedVoice = MutableStateFlow<Voice?>(null)
    val selectedVoice: StateFlow<Voice?> = _selectedVoice.asStateFlow()
    
    private val _isDownloading = MutableStateFlow(false)
    val isDownloading: StateFlow<Boolean> = _isDownloading.asStateFlow()
    
    private val _playbackSpeed = MutableStateFlow(1.0f)
    val playbackSpeed: StateFlow<Float> = _playbackSpeed.asStateFlow()
    
    private val _playbackPitch = MutableStateFlow(1.0f)
    val playbackPitch: StateFlow<Float> = _playbackPitch.asStateFlow()
    
    private val _autoRead = MutableStateFlow(true)
    val autoRead: StateFlow<Boolean> = _autoRead.asStateFlow()
    
    private val _darkMode = MutableStateFlow(true)
    val darkMode: StateFlow<Boolean> = _darkMode.asStateFlow()
    
    private val _overlayOpacity = MutableStateFlow(0.95f)
    val overlayOpacity: StateFlow<Float> = _overlayOpacity.asStateFlow()
    
    init {
        viewModelScope.launch {
            settingsDataStore.settings.collect { settings ->
                _playbackSpeed.value = settings.playbackSpeed
                _playbackPitch.value = settings.playbackPitch
                _autoRead.value = settings.autoReadEnabled
                _darkMode.value = settings.darkModeEnabled
                _overlayOpacity.value = settings.overlayOpacity
                
                if (settings.selectedVoiceId.isNotEmpty()) {
                    _selectedVoice.value = _availableVoices.value.find { it.id == settings.selectedVoiceId }
                }
            }
        }
        
        initTts()
    }
    
    private fun initTts() {
        textToSpeech = TextToSpeech(application) { status ->
            if (status == TextToSpeech.SUCCESS) {
                isTtsReady = true
            }
        }
    }
    
    private fun getDefaultVoices(): List<Voice> {
        return listOf(
            Voice(
                id = "en_US_amy_medium",
                name = "Amy (US English)",
                language = "English (US)",
                gender = VoiceGender.FEMALE,
                quality = VoiceQuality.MEDIUM,
                isDownloaded = true
            ),
            Voice(
                id = "en_US_ryan_medium",
                name = "Ryan (US English)",
                language = "English (US)",
                gender = VoiceGender.MALE,
                quality = VoiceQuality.MEDIUM,
                isDownloaded = true
            ),
            Voice(
                id = "en_GB_alan_medium",
                name = "Alan (UK English)",
                language = "English (UK)",
                gender = VoiceGender.MALE,
                quality = VoiceQuality.MEDIUM,
                isDownloaded = false
            ),
            Voice(
                id = "en_GB_sonia_medium",
                name = "Sonia (UK English)",
                language = "English (UK)",
                gender = VoiceGender.FEMALE,
                quality = VoiceQuality.MEDIUM,
                isDownloaded = false
            )
        )
    }
    
    fun selectVoice(voice: Voice) {
        viewModelScope.launch {
            _selectedVoice.value = voice
            settingsDataStore.updateSelectedVoice(voice.id)
        }
    }
    
    fun downloadVoice(voice: Voice) {
        viewModelScope.launch {
            _isDownloading.value = true
            // Simulate download
            kotlinx.coroutines.delay(2000)
            
            val updatedVoices = _availableVoices.value.map {
                if (it.id == voice.id) it.copy(isDownloaded = true) else it
            }
            _availableVoices.value = updatedVoices
            
            settingsDataStore.addDownloadedVoice(voice.id)
            _isDownloading.value = false
        }
    }
    
    fun deleteVoice(voice: Voice) {
        viewModelScope.launch {
            val updatedVoices = _availableVoices.value.map {
                if (it.id == voice.id) it.copy(isDownloaded = false) else it
            }
            _availableVoices.value = updatedVoices
            
            settingsDataStore.removeDownloadedVoice(voice.id)
        }
    }
    
    fun updateSpeed(speed: Float) {
        viewModelScope.launch {
            _playbackSpeed.value = speed
            settingsDataStore.updatePlaybackSpeed(speed)
        }
    }
    
    fun updatePitch(pitch: Float) {
        viewModelScope.launch {
            _playbackPitch.value = pitch
            settingsDataStore.updatePlaybackPitch(pitch)
        }
    }
    
    fun updateAutoRead(enabled: Boolean) {
        viewModelScope.launch {
            _autoRead.value = enabled
            settingsDataStore.updateAutoRead(enabled)
        }
    }
    
    fun updateDarkMode(enabled: Boolean) {
        viewModelScope.launch {
            _darkMode.value = enabled
        }
    }
    
    fun updateOverlayOpacity(opacity: Float) {
        viewModelScope.launch {
            _overlayOpacity.value = opacity
            settingsDataStore.updateOverlayOpacity(opacity)
        }
    }
    
    fun testSpeech() {
        if (!isTtsReady) return
        
        textToSpeech?.setSpeechRate(_playbackSpeed.value)
        textToSpeech?.setPitch(_playbackPitch.value)
        textToSpeech?.speak(
            "Hello! This is a test of the Sonata text-to-speech engine. It should sound natural and pleasant.",
            TextToSpeech.QUEUE_FLUSH,
            null,
            "test_utterance"
        )
        
        // Start foreground service
        val serviceIntent = Intent(application, TtsPlaybackService::class.java)
        application.startService(serviceIntent)
    }
    
    fun clearCache() {
        viewModelScope.launch {
            settingsDataStore.clearCache()
            _availableVoices.value = _availableVoices.value.map { it.copy(isDownloaded = false) }
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        textToSpeech?.stop()
        textToSpeech?.shutdown()
    }
}