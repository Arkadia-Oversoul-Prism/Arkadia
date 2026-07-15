package com.arkadia.sonata

import android.content.ComponentName
import android.content.Intent
import android.content.ServiceConnection
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.provider.Settings
import android.widget.SeekBar
import androidx.appcompat.app.AppCompatActivity
import com.arkadia.sonata.databinding.ActivityMainBinding
import com.google.android.material.snackbar.Snackbar

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var prefs: Prefs

    private var speechService: SpeechService? = null
    private val conn = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, binder: IBinder) {
            speechService = (binder as SpeechService.LocalBinder).getService()
            speechService?.onStart    = { updateUi() }
            speechService?.onPause    = { updateUi() }
            speechService?.onResume   = { updateUi() }
            speechService?.onComplete = { updateUi(); stopProgressUpdater() }
            speechService?.onError    = { msg -> 
                updateUi(); stopProgressUpdater()
                Snackbar.make(binding.root, msg, Snackbar.LENGTH_LONG).show()
            }
        }
        override fun onServiceDisconnected(name: ComponentName) {
            speechService = null
            updateUi()
        }
    }

    private val progressHandler = Handler(Looper.getMainLooper())
    private val progressRunnable = object : Runnable {
        override fun run() {
            speechService?.let { svc ->
                val pos = svc.currentPositionMs
                val dur = svc.durationMs
                if (dur > 0) {
                    binding.seekProgress.max = dur
                    binding.seekProgress.progress = pos
                    val posSec = pos / 1000
                    val durSec = dur / 1000
                    binding.tvTimeElapsed.text = String.format("%d:%02d", posSec / 60, posSec % 60)
                    binding.tvTimeTotal.text = String.format("%d:%02d", durSec / 60, durSec % 60)
                }
            }
            progressHandler.postDelayed(this, 100)
        }
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs   = Prefs(this)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupSpeedSeekBar()
        setupPlaybackControls()
        setupButtons()
        checkOverlayPermission()
        checkApiKeySetup()
    }

    override fun onStart() {
        super.onStart()
        bindService(Intent(this, SpeechService::class.java), conn, BIND_AUTO_CREATE)
    }

    override fun onStop() {
        super.onStop()
        runCatching { unbindService(conn) }
        stopProgressUpdater()
    }

    private fun startProgressUpdater() {
        progressHandler.removeCallbacks(progressRunnable)
        progressHandler.post(progressRunnable)
    }

    private fun stopProgressUpdater() {
        progressHandler.removeCallbacks(progressRunnable)
    }

    // ── UI setup ──────────────────────────────────────────────────────────

    private fun setupSpeedSeekBar() {
        val speeds = listOf(0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 1.75f, 2.0f)
        binding.seekSpeed.max      = speeds.size - 1
        binding.seekSpeed.progress = speeds.indexOfFirst { it == prefs.speed }.coerceAtLeast(2)
        updateSpeedLabel(prefs.speed)

        binding.seekSpeed.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar, progress: Int, fromUser: Boolean) {
                val s = speeds[progress]
                prefs.speed = s
                updateSpeedLabel(s)
            }
            override fun onStartTrackingTouch(sb: SeekBar) {}
            override fun onStopTrackingTouch(sb: SeekBar) {}
        })
    }

    private fun updateSpeedLabel(speed: Float) {
        binding.tvSpeedLabel.text = "${speed}×"
    }

    private fun setupPlaybackControls() {
        binding.seekProgress.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(sb: SeekBar, progress: Int, fromUser: Boolean) {
                if (fromUser) speechService?.seekTo(progress)
            }
            override fun onStartTrackingTouch(sb: SeekBar) {}
            override fun onStopTrackingTouch(sb: SeekBar) {}
        })
    }

    private fun setupButtons() {
        binding.btnSpeak.setOnClickListener {
            val text = binding.etTestInput.text?.toString()?.trim() ?: ""
            if (text.isEmpty()) {
                Snackbar.make(binding.root, "Enter some text to speak", Snackbar.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            // Check if API key is configured
            if (!prefs.hasElevenLabsKey() && prefs.edgeTtsUrl.isBlank()) {
                Snackbar.make(binding.root, "Configure ElevenLabs key in Settings first", Snackbar.LENGTH_LONG)
                    .setAction("Settings") {
                        startActivity(Intent(this, SettingsActivity::class.java))
                    }.show()
                return@setOnClickListener
            }

            val intent = Intent(this, SpeechService::class.java).apply {
                action = SpeechService.ACTION_SPEAK
                putExtra(SpeechService.EXTRA_TEXT,  text)
                putExtra(SpeechService.EXTRA_LABEL, "Sonata Reader")
            }
            startForegroundService(intent)
        }

        binding.btnPlayPause.setOnClickListener {
            speechService?.let { svc ->
                when {
                    svc.isPlaying -> { svc.pause(); updateUi() }
                    svc.isPausedState -> { svc.resume(); updateUi() }
                    else -> binding.btnSpeak.callOnClick()
                }
            } ?: binding.btnSpeak.callOnClick()
        }

        binding.btnStop.setOnClickListener {
            speechService?.stop()
            stopProgressUpdater()
            updateUi()
        }

        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }

        binding.btnKnowledgeOs.setOnClickListener {
            if (prefs.edgeTtsUrl.isBlank()) {
                Snackbar.make(binding.root, "Set your Arkadia backend URL in Settings", Snackbar.LENGTH_LONG)
                    .setAction("Settings") {
                        startActivity(Intent(this, SettingsActivity::class.java))
                    }.show()
            } else {
                startActivity(Intent(this, KnowledgeActivity::class.java))
            }
        }
    }

    private fun checkOverlayPermission() {
        if (!Settings.canDrawOverlays(this)) {
            binding.bannerOverlay.visibility = android.view.View.VISIBLE
            binding.bannerOverlay.setOnClickListener {
                startActivity(Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:$packageName")
                ))
            }
        } else {
            binding.bannerOverlay.visibility = android.view.View.GONE
        }
    }

    private fun checkApiKeySetup() {
        if (!prefs.hasElevenLabsKey()) {
            binding.tvApiStatus.text = "⚠ No ElevenLabs key — tap Settings to add"
            binding.tvApiStatus.visibility = android.view.View.VISIBLE
        } else {
            binding.tvApiStatus.visibility = android.view.View.GONE
        }
    }

    private fun updateUi() {
        runOnUiThread {
            val playing = speechService?.isPlaying == true
            val paused = speechService?.isPausedState == true
            val active = playing || paused

            // Update play/pause button
            binding.btnPlayPause.text = when {
                playing -> "⏸"
                paused -> "▶"
                else -> "▶"
            }

            // Show/hide playback bar
            binding.playbackBar.visibility = if (active) android.view.View.VISIBLE else android.view.View.GONE

            // Progress bar
            if (playing) {
                startProgressUpdater()
            } else if (!paused) {
                stopProgressUpdater()
                binding.seekProgress.progress = 0
            }

            // Disable speak button while playing
            binding.btnSpeak.isEnabled = !playing
        }
    }
}
