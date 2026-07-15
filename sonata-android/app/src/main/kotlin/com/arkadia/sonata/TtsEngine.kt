package com.arkadia.sonata

import android.content.Context
import android.media.MediaPlayer
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.util.Locale
import java.util.UUID
import java.util.concurrent.TimeUnit

private const val TAG = "SonataTts"

/**
 * Three-tier TTS engine.
 *
 *  Tier 1 (ElevenLabs) — neural quality TTS via ElevenLabs API
 *  Tier 2 (Edge TTS)  — calls the Arkadia Oracle Temple /api/tts endpoint
 *  Tier 3 (Android)   — offline Android built-in TextToSpeech
 *
 * The engine exposes a simple [speak]/[pause]/[resume]/[stop] interface.
 * Callers register a [Listener] to receive lifecycle callbacks.
 */
class TtsEngine(
    private val context: Context,
    private val prefs: Prefs,
) {
    interface Listener {
        fun onStart()
        fun onPaused()
        fun onResumed()
        fun onComplete()
        fun onError(msg: String)
        fun onProgress(currentMs: Int, totalMs: Int)
    }

    // ── Android TTS (tier 3) ───────────────────────────────────────────────
    private var androidTts: TextToSpeech? = null
    private var androidTtsReady = false

    // ── MediaPlayer for ElevenLabs / Edge TTS audio (tiers 1-2) ───────────
    private var mediaPlayer: MediaPlayer? = null
    private var isPaused = false
    private var currentFile: File? = null

    // ── Coroutine scope (tied to engine lifecycle) ─────────────────────────
    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private val http = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    var listener: Listener? = null
    private var currentMode: Mode = Mode.IDLE

    enum class Mode { IDLE, ELEVENLABS, EDGE_TTS, ANDROID_TTS }

    // ── Initialise Android TTS ─────────────────────────────────────────────
    fun init(onReady: (() -> Unit)? = null) {
        androidTts = TextToSpeech(context) { status ->
            androidTtsReady = status == TextToSpeech.SUCCESS
            if (androidTtsReady) {
                androidTts?.language = Locale.US
                Log.i(TAG, "Android TTS ready")
                onReady?.invoke()
            } else {
                Log.w(TAG, "Android TTS init failed (status=$status)")
            }
        }
    }

    // ── Public API ──────────────────────────────────────────────────────────

    fun speak(text: String) {
        stop()
        isPaused = false

        // Try ElevenLabs first if configured
        if (prefs.preferElevenLabs && prefs.hasElevenLabsKey()) {
            speakElevenLabs(text)
        } else {
            val url = prefs.edgeTtsUrl.trim()
            if (url.isNotEmpty()) {
                speakEdge(text, url)
            } else {
                speakAndroid(text)
            }
        }
    }

    fun pause() {
        when (currentMode) {
            Mode.ELEVENLABS, Mode.EDGE_TTS -> {
                mediaPlayer?.pause()
                isPaused = true
                listener?.onPaused()
            }
            Mode.ANDROID_TTS -> {
                androidTts?.stop()
                isPaused = true
                listener?.onPaused()
            }
            Mode.IDLE -> {}
        }
    }

    fun resume() {
        when (currentMode) {
            Mode.ELEVENLABS, Mode.EDGE_TTS -> {
                if (isPaused) {
                    mediaPlayer?.start()
                    isPaused = false
                    listener?.onResumed()
                }
            }
            Mode.ANDROID_TTS -> {
                listener?.onResumed()
            }
            Mode.IDLE -> {}
        }
    }

    fun stop() {
        mediaPlayer?.apply {
            try { if (isPlaying) stop() } catch (e: Exception) {}
            try { reset() } catch (e: Exception) {}
            try { release() } catch (e: Exception) {}
        }
        mediaPlayer = null
        currentFile?.delete()
        currentFile = null
        androidTts?.stop()
        currentMode = Mode.IDLE
        isPaused = false
    }

    fun seekTo(positionMs: Int) {
        if (currentMode == Mode.ELEVENLABS || currentMode == Mode.EDGE_TTS) {
            mediaPlayer?.seekTo(positionMs)
        }
    }

    val isPlaying: Boolean
        get() = when (currentMode) {
            Mode.ELEVENLABS, Mode.EDGE_TTS -> mediaPlayer?.isPlaying == true
            Mode.ANDROID_TTS -> androidTts?.isSpeaking == true
            Mode.IDLE -> false
        }

    val isPausedState: Boolean get() = isPaused

    val currentPositionMs: Int
        get() = try { mediaPlayer?.currentPosition ?: 0 } catch (e: Exception) { 0 }

    val durationMs: Int
        get() = try { mediaPlayer?.duration ?: 0 } catch (e: Exception) { 0 }

    fun shutdown() {
        stop()
        androidTts?.shutdown()
        androidTts = null
        http.dispatcher.executorService.shutdown()
    }

    // ── Tier 1: ElevenLabs ──────────────────────────────────────────────────

    private fun speakElevenLabs(text: String) {
        currentMode = Mode.ELEVENLABS
        listener?.onStart()

        scope.launch {
            try {
                // Try primary key first, then fallback to secondary
                val key = prefs.getActiveElevenLabsKey()
                if (key.isBlank()) {
                    withContext(Dispatchers.Main) {
                        listener?.onError("No ElevenLabs API key configured")
                    }
                    return@launch
                }

                val voiceId = prefs.elevenLabsVoice
                val speed = prefs.speed.coerceIn(0.5f, 2.0f)

                // ElevenLabs TTS endpoint
                val url = "https://api.elevenlabs.io/v1/text-to-speech/$voiceId/stream"

                val jsonBody = JSONObject().apply {
                    put("text", text)
                    put("model_id", "eleven_monolingual_v1")
                    put("voice_settings", JSONObject().apply {
                        put("stability", 0.5)
                        put("similarity_boost", 0.75)
                    })
                }

                val req = Request.Builder()
                    .url(url)
                    .post(jsonBody.toString().toRequestBody("application/json".toMediaType()))
                    .addHeader("xi-api-key", key)
                    .addHeader("Accept", "audio/mpeg")
                    .build()

                val resp = http.newCall(req).execute()

                when {
                    resp.code == 401 -> {
                        // Try second key if first failed
                        val altKey = if (prefs.elevenLabsKey1 == key) prefs.elevenLabsKey2 else prefs.elevenLabsKey1
                        if (altKey.isNotBlank()) {
                            val altReq = req.newBuilder()
                                .addHeader("xi-api-key", altKey)
                                .build()
                            val altResp = http.newCall(altReq).execute()
                            if (altResp.isSuccessful) {
                                val bytes = altResp.body?.bytes() ?: throw RuntimeException("Empty body")
                                val tmp = File(context.cacheDir, "sonata_el_${UUID.randomUUID()}.mp3")
                                tmp.writeBytes(bytes)
                                withContext(Dispatchers.Main) { playFile(tmp) }
                                return@launch
                            }
                        }
                        throw RuntimeException("ElevenLabs API error: Invalid API key")
                    }
                    resp.isSuccessful -> {
                        val bytes = resp.body?.bytes() ?: throw RuntimeException("Empty body")
                        val tmp = File(context.cacheDir, "sonata_el_${UUID.randomUUID()}.mp3")
                        tmp.writeBytes(bytes)
                        withContext(Dispatchers.Main) { playFile(tmp) }
                    }
                    else -> throw RuntimeException("ElevenLabs API error: ${resp.code}")
                }
            } catch (e: Exception) {
                Log.e(TAG, "ElevenLabs failed: ${e.message}")
                withContext(Dispatchers.Main) {
                    // Fallback to Edge TTS or Android TTS
                    val url = prefs.edgeTtsUrl.trim()
                    if (url.isNotEmpty()) {
                        speakEdge(text, url)
                    } else {
                        speakAndroid(text)
                    }
                }
            }
        }
    }

    // ── Tier 2: Edge TTS ───────────────────────────────────────────────────

    private fun speakEdge(text: String, baseUrl: String) {
        currentMode = Mode.EDGE_TTS
        listener?.onStart()

        scope.launch {
            try {
                val body = JSONObject().apply {
                    put("text", text)
                    put("voice", prefs.elevenLabsVoice)
                    put("speed", prefs.speed.toDouble())
                }.toString()

                val req = Request.Builder()
                    .url("${baseUrl.trimEnd('/')}/api/tts")
                    .post(body.toRequestBody("application/json".toMediaType()))
                    .build()

                val resp = http.newCall(req).execute()
                if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code}")

                val bytes = resp.body?.bytes() ?: throw RuntimeException("Empty body")
                val tmp = File(context.cacheDir, "sonata_edge_${UUID.randomUUID()}.mp3")
                tmp.writeBytes(bytes)

                withContext(Dispatchers.Main) { playFile(tmp) }
            } catch (e: Exception) {
                Log.w(TAG, "Edge TTS failed: ${e.message}; falling back to Android TTS")
                withContext(Dispatchers.Main) { speakAndroid(text) }
            }
        }
    }

    private fun playFile(file: File) {
        currentFile = file
        mediaPlayer = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            prepare()
            setOnCompletionListener {
                currentMode = Mode.IDLE
                file.delete()
                currentFile = null
                listener?.onComplete()
            }
            setOnErrorListener { _, what, extra ->
                Log.e(TAG, "MediaPlayer error: what=$what, extra=$extra")
                currentMode = Mode.IDLE
                file.delete()
                currentFile = null
                listener?.onError("Playback error")
                true
            }
            start()
        }
    }

    // ── Tier 3: Android TTS (offline) ──────────────────────────────────────

    private fun speakAndroid(text: String) {
        if (!androidTtsReady) {
            listener?.onError("TTS not initialised")
            return
        }
        currentMode = Mode.ANDROID_TTS

        androidTts?.apply {
            setSpeechRate(prefs.speed)
            setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) { listener?.onStart() }
                override fun onDone(utteranceId: String?) {
                    currentMode = Mode.IDLE
                    listener?.onComplete()
                }
                @Deprecated("Deprecated")
                override fun onError(utteranceId: String?) {
                    currentMode = Mode.IDLE
                    listener?.onError("Android TTS error")
                }
            })
            speak(text, TextToSpeech.QUEUE_FLUSH, null, "sonata_utt_${System.currentTimeMillis()}")
        }
        listener?.onStart()
    }
}
