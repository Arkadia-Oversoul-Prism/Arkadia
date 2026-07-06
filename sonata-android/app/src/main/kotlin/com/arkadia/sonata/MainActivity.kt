package com.arkadia.sonata

import android.content.ComponentName
import android.content.Intent
import android.content.ServiceConnection
import android.net.Uri
import android.os.Bundle
import android.os.IBinder
import android.provider.Settings
import android.widget.ArrayAdapter
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
            speechService?.onComplete = { updateUi() }
        }
        override fun onServiceDisconnected(name: ComponentName) {
            speechService = null
            updateUi()
        }
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs   = Prefs(this)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupVoiceSpinner()
        setupSpeedSeekBar()
        setupButtons()
        checkOverlayPermission()
    }

    override fun onStart() {
        super.onStart()
        bindService(Intent(this, SpeechService::class.java), conn, BIND_AUTO_CREATE)
    }

    override fun onStop() {
        super.onStop()
        runCatching { unbindService(conn) }
    }

    // ── UI setup ──────────────────────────────────────────────────────────

    private val voiceKeys = listOf("aria", "jenny", "sonia", "christopher", "george", "ryan")
    private val voiceLabels = listOf(
        "Aria — Warm US female",
        "Jenny — Clear US female",
        "Sonia — British female",
        "Christopher — US male",
        "George — British male",
        "Ryan — Casual US male",
    )

    private fun setupVoiceSpinner() {
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, voiceLabels)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        binding.spinnerVoice.adapter  = adapter
        binding.spinnerVoice.setSelection(voiceKeys.indexOf(prefs.voice).coerceAtLeast(0))
        binding.spinnerVoice.onItemSelectedListener =
            object : android.widget.AdapterView.OnItemSelectedListener {
                override fun onItemSelected(p: android.widget.AdapterView<*>, v: android.view.View?, pos: Int, id: Long) {
                    prefs.voice = voiceKeys[pos]
                }
                override fun onNothingSelected(p: android.widget.AdapterView<*>) {}
            }
    }

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

    private fun setupButtons() {
        binding.btnSpeak.setOnClickListener {
            val text = binding.etTestInput.text?.toString()?.trim() ?: return@setOnClickListener
            if (text.isEmpty()) return@setOnClickListener

            val intent = Intent(this, SpeechService::class.java).apply {
                action = SpeechService.ACTION_SPEAK
                putExtra(SpeechService.EXTRA_TEXT,  text)
                putExtra(SpeechService.EXTRA_LABEL, "SONATA TEST")
            }
            startForegroundService(intent)
        }

        binding.btnPause.setOnClickListener  { speechService?.pause()  }
        binding.btnStop.setOnClickListener   { speechService?.stop()   }

        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }

        // ── Knowledge OS ──────────────────────────────────────────────
        binding.btnKnowledgeOs.setOnClickListener {
            if (prefs.edgeTtsUrl.isBlank()) {
                Snackbar.make(
                    binding.root,
                    "Set your Arkadia backend URL in Settings first",
                    Snackbar.LENGTH_LONG
                ).setAction("Settings") {
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

    private fun updateUi() {
        runOnUiThread {
            val playing = speechService?.isPlaying == true
            binding.btnPause.isEnabled = playing || speechService?.isPaused == true
            binding.btnStop.isEnabled  = playing || speechService?.isPaused == true
            binding.btnPause.text      = if (speechService?.isPaused == true) "Resume" else "Pause"
        }
    }
}
