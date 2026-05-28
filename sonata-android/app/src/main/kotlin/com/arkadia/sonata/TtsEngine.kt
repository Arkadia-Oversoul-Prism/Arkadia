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
 * Two-tier TTS engine.
 *
 *  Tier 1 (online, neural quality) — calls the Arkadia Oracle Temple /api/tts
 *    endpoint, streams the MP3, plays via MediaPlayer.
 *  Tier 2 (offline, instant) — Android built-in TextToSpeech.
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
    }

    // ── Android TTS (tier 2) ───────────────────────────────────────────────
    private var androidTts: TextToSpeech? = null
    private var androidTtsReady = false

    // ── MediaPlayer for Edge TTS audio (tier 1) ───────────────────────────
    private var mediaPlayer: MediaPlayer? = null
    private var isPaused = false

    // ── Coroutine scope (tied to engine lifecycle) ─────────────────────────
    private val scope  = CoroutineScope(Dispatchers.IO + Job())
    private val http   = OkHttpClient.Builder()
        .connectTimeout(8, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    var listener: Listener? = null
    private var currentMode: Mode = Mode.IDLE

    enum class Mode { IDLE, EDGE_TTS, ANDROID_TTS }

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

        val url = prefs.edgeTtsUrl.trim()
        if (prefs.preferEdgeTts && url.isNotEmpty()) {
            speakEdge(text, url)
        } else {
            speakAndroid(text)
        }
    }

    fun pause() {
        when (currentMode) {
            Mode.EDGE_TTS -> {
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
            Mode.EDGE_TTS -> {
                if (isPaused) {
                    mediaPlayer?.start()
                    isPaused = false
                    listener?.onResumed()
                }
            }
            Mode.ANDROID_TTS -> {
                // Android TTS cannot resume mid-utterance; restart not ideal
                listener?.onResumed()
            }
            Mode.IDLE -> {}
        }
    }

    fun stop() {
        mediaPlayer?.apply { if (isPlaying) stop(); reset(); release() }
        mediaPlayer = null
        androidTts?.stop()
        currentMode = Mode.IDLE
        isPaused = false
    }

    val isPlaying: Boolean
        get() = when (currentMode) {
            Mode.EDGE_TTS    -> mediaPlayer?.isPlaying == true
            Mode.ANDROID_TTS -> androidTts?.isSpeaking == true
            Mode.IDLE        -> false
        }

    val isPausedState: Boolean get() = isPaused

    fun shutdown() {
        stop()
        androidTts?.shutdown()
        androidTts = null
        http.dispatcher.executorService.shutdown()
    }

    // ── Tier 1: Edge TTS (network) ─────────────────────────────────────────

    private fun speakEdge(text: String, baseUrl: String) {
        currentMode = Mode.EDGE_TTS
        listener?.onStart()

        scope.launch {
            try {
                val body = JSONObject().apply {
                    put("text", text)
                    put("voice", prefs.voice)
                    put("speed", prefs.speed.toDouble())
                }.toString()

                val req = Request.Builder()
                    .url("${baseUrl.trimEnd('/')}/api/tts")
                    .post(body.toRequestBody("application/json".toMediaType()))
                    .build()

                val resp = http.newCall(req).execute()
                if (!resp.isSuccessful) throw RuntimeException("HTTP ${resp.code}")

                val bytes = resp.body?.bytes()
                    ?: throw RuntimeException("Empty body")

                // Write to temp file (MediaPlayer needs a URI or file path)
                val tmp = File(context.cacheDir, "sonata_${UUID.randomUUID()}.mp3")
                tmp.writeBytes(bytes)

                withContext(Dispatchers.Main) {
                    playFile(tmp)
                }
            } catch (e: Exception) {
                Log.w(TAG, "Edge TTS failed: ${e.message}; falling back to Android TTS")
                withContext(Dispatchers.Main) {
                    speakAndroid(text)
                }
            }
        }
    }

    private fun playFile(file: File) {
        mediaPlayer = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            prepare()
            setOnCompletionListener {
                currentMode = Mode.IDLE
                file.delete()
                listener?.onComplete()
            }
            setOnErrorListener { _, _, _ ->
                currentMode = Mode.IDLE
                file.delete()
                listener?.onError("MediaPlayer error")
                true
            }
            start()
        }
    }

    // ── Tier 2: Android TTS (offline) ──────────────────────────────────────

    private fun speakAndroid(text: String) {
        if (!androidTtsReady) {
            listener?.onError("TTS not initialised")
            return
        }
        currentMode = Mode.ANDROID_TTS

        androidTts?.apply {
            setSpeechRate(prefs.speed)
            setPitch(prefs.pitch)
            setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    listener?.onStart()
                }
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
