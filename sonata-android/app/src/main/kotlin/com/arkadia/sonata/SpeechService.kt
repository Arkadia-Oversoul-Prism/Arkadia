package com.arkadia.sonata

import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.media.session.MediaSession
import android.media.session.PlaybackState
import android.os.Binder
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationCompat.Action

/**
 * Foreground service that owns a [TtsEngine] instance.
 * Activities and the overlay bind to it via [LocalBinder].
 *
 * Commands (via startForegroundService + intent action):
 *   ACTION_SPEAK  — extras: EXTRA_TEXT, EXTRA_LABEL
 *   ACTION_PAUSE
 *   ACTION_RESUME
 *   ACTION_STOP
 */
class SpeechService : Service() {

    inner class LocalBinder : Binder() {
        fun getService(): SpeechService = this@SpeechService
    }

    private val binder = LocalBinder()
    private lateinit var tts: TtsEngine
    private lateinit var prefs: Prefs
    private lateinit var mediaSession: MediaSession

    private var currentText  = ""
    private var currentLabel = "SONATA"

    // ── Lifecycle callbacks exposed to bound clients ────────────────────────
    var onStart:    (() -> Unit)? = null
    var onPause:    (() -> Unit)? = null
    var onResume:   (() -> Unit)? = null
    var onComplete: (() -> Unit)? = null
    var onError: ((String) -> Unit)? = null

    // ── Service lifecycle ──────────────────────────────────────────────────

    override fun onCreate() {
        super.onCreate()
        prefs = Prefs(this)
        tts   = TtsEngine(this, prefs).also { it.init() }
        setupMediaSession()
        tts.listener = ttsListener
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_SPEAK  -> {
                currentText  = intent.getStringExtra(EXTRA_TEXT)  ?: return START_NOT_STICKY
                currentLabel = intent.getStringExtra(EXTRA_LABEL) ?: "SONATA"
                startForeground(SonataApp.NOTIF_ID, buildNotification(playing = true))
                tts.speak(currentText)
            }
            ACTION_PAUSE  -> { tts.pause();  updateNotification(playing = false) }
            ACTION_RESUME -> { tts.resume(); updateNotification(playing = true)  }
            ACTION_STOP   -> stopSelf()
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent): IBinder = binder

    override fun onDestroy() {
        tts.shutdown()
        mediaSession.release()
        super.onDestroy()
    }

    // ── Public control surface (used when bound) ───────────────────────────

    fun pause()  { tts.pause();  updateNotification(playing = false) }
    fun resume() { tts.resume(); updateNotification(playing = true)  }
    fun stop()   { tts.stop();   stopForeground(STOP_FOREGROUND_REMOVE); stopSelf() }
    fun seekTo(positionMs: Int) { tts.seekTo(positionMs) }

    val isPlaying get() = tts.isPlaying
    val isPaused  get() = tts.isPausedState
    val currentPositionMs: Int get() = tts.currentPositionMs
    val durationMs: Int get() = tts.durationMs

    // ── TTS listener ───────────────────────────────────────────────────────

    private val ttsListener = object : TtsEngine.Listener {
        override fun onStart()           { updateNotification(true);  onStart?.invoke() }
        override fun onPaused()          { updateNotification(false); onPause?.invoke() }
        override fun onResumed()         { updateNotification(true);  onResume?.invoke() }
        override fun onComplete()        {
            stopForeground(STOP_FOREGROUND_REMOVE)
            onComplete?.invoke()
        }
        override fun onError(msg: String) {
            stopForeground(STOP_FOREGROUND_REMOVE)
            onError?.invoke(msg)
            stopSelf()
        }
        override fun onProgress(currentMs: Int, totalMs: Int) { /* used by UI */ }
    }

    // ── Notification ───────────────────────────────────────────────────────

    private fun buildNotification(playing: Boolean): Notification {
        val pauseResumeAction = if (playing) ACTION_PAUSE else ACTION_RESUME
        val pauseResumeLabel  = if (playing) "Pause"     else "Resume"
        val pauseResumeIcon   = if (playing)
            android.R.drawable.ic_media_pause else android.R.drawable.ic_media_play

        val pauseResumeIntent = PendingIntent.getService(
            this, 0,
            Intent(this, SpeechService::class.java).apply { action = pauseResumeAction },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val stopIntent = PendingIntent.getService(
            this, 1,
            Intent(this, SpeechService::class.java).apply { action = ACTION_STOP },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val openIntent = PendingIntent.getActivity(
            this, 2,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Update media session playback state
        val state = PlaybackState.Builder()
            .setState(
                if (playing) PlaybackState.STATE_PLAYING else PlaybackState.STATE_PAUSED,
                PlaybackState.PLAYBACK_POSITION_UNKNOWN,
                1f
            )
            .setActions(PlaybackState.ACTION_PLAY_PAUSE or PlaybackState.ACTION_STOP)
            .build()
        mediaSession.setPlaybackState(state)

        val preview = currentText.take(80) + if (currentText.length > 80) "…" else ""

        return NotificationCompat.Builder(this, SonataApp.CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_sonata)
            .setContentTitle(currentLabel)
            .setContentText(preview)
            .setContentIntent(openIntent)
            .addAction(pauseResumeIcon, pauseResumeLabel, pauseResumeIntent)
            .addAction(android.R.drawable.ic_delete, "Stop", stopIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(playing)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .build()
    }

    private fun updateNotification(playing: Boolean) {
        getSystemService(NotificationManager::class.java)
            .notify(SonataApp.NOTIF_ID, buildNotification(playing))
    }

    private fun setupMediaSession() {
        mediaSession = MediaSession(this, "SonataSession").apply {
            setCallback(object : MediaSession.Callback() {
                override fun onPlay()  { resume() }
                override fun onPause() { pause()  }
                override fun onStop()  { stop()   }
            })
            isActive = true
        }
    }

    companion object {
        const val ACTION_SPEAK  = "com.arkadia.sonata.SPEAK"
        const val ACTION_PAUSE  = "com.arkadia.sonata.PAUSE"
        const val ACTION_RESUME = "com.arkadia.sonata.RESUME"
        const val ACTION_STOP   = "com.arkadia.sonata.STOP"
        const val EXTRA_TEXT    = "text"
        const val EXTRA_LABEL   = "label"
    }
}
