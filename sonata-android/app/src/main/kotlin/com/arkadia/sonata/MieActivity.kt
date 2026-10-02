package com.arkadia.sonata

import android.Manifest
import android.content.pm.PackageManager
import android.media.MediaPlayer
import android.os.Bundle
import android.os.SystemClock
import android.view.MotionEvent
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.arkadia.sonata.databinding.ActivityMieBinding
import java.io.File

class MieActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMieBinding
    private lateinit var recorder: MieAudioRecorder
    private var mediaPlayer: MediaPlayer? = null
    private var captureStartedAt = 0L
    private var lastCapture: File? = null

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) beginCapture() else showStatus("Microphone permission is required to capture a musical idea.")
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMieBinding.inflate(layoutInflater)
        setContentView(binding.root)

        recorder = MieAudioRecorder(File(filesDir, "mie/captures"))
        binding.captureButton.setOnTouchListener { _, event ->
            when (event.actionMasked) {
                MotionEvent.ACTION_DOWN -> {
                    if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                        permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    } else {
                        beginCapture()
                    }
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    if (recorder.isRecording()) finishCapture()
                    true
                }
                else -> true
            }
        }

        binding.playButton.setOnClickListener { playLastCapture() }
        binding.keepButton.setOnClickListener {
            showStatus("Kept locally. The original remains preserved for the next transformation pass.")
        }
        binding.changeButton.setOnClickListener {
            showStatus("Change is the next experimental boundary. Original capture remains preserved.")
        }
    }

    private fun beginCapture() {
        stopPlayback()
        captureStartedAt = SystemClock.elapsedRealtime()
        binding.captureButton.text = "Release to finish"
        binding.captureButton.isPressed = true
        binding.objectCard.visibility = View.VISIBLE
        binding.objectType.text = "CAPTURING…"
        binding.objectDetail.text = "Listening"
        binding.objectJson.text = ""
        if (!recorder.start()) {
            binding.captureButton.text = "Hold to capture"
            binding.captureButton.isPressed = false
            showStatus("Capture could not start. Check microphone access and retry.")
        } else {
            showStatus("Listening…")
        }
    }

    private fun finishCapture() {
        recorder.stop()
        binding.captureButton.text = "Hold to capture"
        binding.captureButton.isPressed = false
        val elapsed = SystemClock.elapsedRealtime() - captureStartedAt
        showStatus("Captured in " + String.format("%.1f", elapsed / 1000f) + "s. Interpreting…")

        Thread {
            val file = recorder.lastFile
            if (file == null || !file.exists() || file.length() <= 44L) {
                runOnUiThread { showStatus("Capture ended without usable audio.") }
                return@Thread
            }
            val interpretation = MieMusicalInterpreter.interpret(file)
            val objectModel = MieMusicalObject(
                sourcePath = file.absolutePath,
                durationMs = recorder.durationMs(file),
                inputType = interpretation.inputType,
                confidence = interpretation.confidence,
                rms = interpretation.rms,
                zeroCrossingRate = interpretation.zeroCrossingRate,
                detectedPitchHz = interpretation.pitchHz,
                detectedMidi = interpretation.midi
            )
            File(file.parentFile, objectModel.id + ".json").writeText(objectModel.toJson())
            runOnUiThread { renderObject(file, objectModel) }
        }.start()
    }

    private fun renderObject(file: File, objectModel: MieMusicalObject) {
        binding.objectCard.visibility = View.VISIBLE
        binding.objectType.text = objectModel.inputType.replace('_', ' ').uppercase()
        val pitch = objectModel.detectedPitchHz?.let { String.format("%.1f Hz", it) } ?: "not detected"
        binding.objectDetail.text =
            String.format("%.2fs · pitch %s · confidence %.0f%%",
                objectModel.durationMs / 1000f, pitch, objectModel.confidence * 100f)
        binding.objectJson.text = objectModel.toJson()
        binding.playButton.isEnabled = true
        binding.keepButton.isEnabled = true
        binding.changeButton.isEnabled = true
        lastCapture = file
        showStatus("Musical object materialized. Original audio preserved.")
    }

    private fun playLastCapture() {
        val file = lastCapture ?: recorder.lastFile ?: return
        stopPlayback()
        mediaPlayer = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            setOnCompletionListener { stopPlayback() }
            setOnErrorListener { _, _, _ ->
                showStatus("Playback failed for this capture.")
                stopPlayback()
                true
            }
            prepare()
            start()
        }
        binding.playButton.text = "STOP"
        showStatus("Playing original capture.")
    }

    private fun stopPlayback() {
        mediaPlayer?.let {
            runCatching { if (it.isPlaying) it.stop() }
            it.release()
        }
        mediaPlayer = null
        binding.playButton.text = "PLAY ORIGINAL"
    }

    private fun showStatus(message: String) {
        runOnUiThread { binding.status.text = message }
    }

    override fun onStop() {
        super.onStop()
        stopPlayback()
        if (recorder.isRecording()) recorder.stop()
    }
}
