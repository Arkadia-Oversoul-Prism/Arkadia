package com.arkadia.sonata

import android.Manifest
import android.content.pm.PackageManager
import android.media.MediaPlayer
import android.os.Bundle
import android.os.SystemClock
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.app.AlertDialog
import kotlin.math.roundToInt
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.arkadia.sonata.databinding.ActivityMieBinding
import java.io.File

class MieActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMieBinding
    private lateinit var recorder: MieAudioRecorder
    private lateinit var sessionStore: MieSessionStore
    private var mediaPlayer: MediaPlayer? = null
    private var captureStartedAt = 0L
    private var lastCapture: File? = null
    private var selectedObject: MieMusicalObject? = null
    private var playingFile: File? = null
    private var playingButton: Button? = null
    private var pauseButton: Button? = null
    private var repeatButton: Button? = null
    private var repeatPlayback = false

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) beginCapture() else showStatus("Microphone permission is required to capture a musical idea.")
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMieBinding.inflate(layoutInflater)
        setContentView(binding.root)

        recorder = MieAudioRecorder(File(filesDir, "mie/captures"))
        sessionStore = MieSessionStore(this)
        renderHistory()
        binding.undoButton.setOnClickListener { undoAction() }
        binding.redoButton.setOnClickListener { redoAction() }
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

        binding.keepButton.setOnClickListener { keepSelectedResult() }
        binding.changeButton.setOnClickListener {
            if (selectedObject?.transformation == null) transformSelectedCapture() else reviseSelectedResult()
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
            sessionStore.addCapture(objectModel)
            runOnUiThread { renderObject(file, objectModel); renderHistory() }
        }.start()
    }

    private fun renderObject(file: File, objectModel: MieMusicalObject) {
        binding.objectCard.visibility = View.VISIBLE
        val namePrefix = objectModel.displayName?.let { "${it} · " } ?: ""
        binding.objectType.text = namePrefix + if (objectModel.transformation == null) "ORIGINAL · ${objectModel.humanType().uppercase()}" else "DERIVED · OCTAVE UP"
        val pitch = objectModel.detectedPitchHz?.let { hz ->
            val note = objectModel.noteName()
            if (note != null) "$note · ${String.format("%.1f Hz", hz)}" else String.format("%.1f Hz", hz)
        } ?: "not detected"
        binding.objectDetail.text =
            String.format("%.2fs · pitch %s · confidence %.0f%%",
                objectModel.durationMs / 1000f, pitch, objectModel.confidence * 100f)
        binding.objectJson.text = objectModel.toJson()
        val isResult = objectModel.transformation != null
        binding.keepButton.isEnabled = isResult
        binding.changeButton.isEnabled = true
        binding.keepButton.text = if (objectModel.loopDecision == "kept") "KEPT ✓" else "KEEP RESULT"
        binding.changeButton.text = when {
            !isResult -> "CHANGE"
            objectModel.loopDecision == "revised" -> "REVISED ✓"
            else -> "REVISE"
        }
        lastCapture = file
        selectedObject = objectModel
        binding.changeButton.text = if (isResult) "REVISE" else "OCTAVE UP"
        showStatus(if (objectModel.transformation == null) "Saved as capture ${objectModel.id.take(8)}. Original audio preserved." else "Result ready. Compare it with the original, then keep or revise.")
    }

    private fun renderHistory() {
        val captures = sessionStore.activeCaptures()
        val deleted = sessionStore.deletedCaptures()
        binding.historyCount.text = captures.size.toString() + " active · " + deleted.size.toString() + " in trash"
        binding.historyList.removeAllViews()

        if (captures.isEmpty() && deleted.isEmpty()) {
            val empty = Button(this).apply {
                text = "No captures yet. Your next idea will appear here."
                isAllCaps = false
                isEnabled = false
            }
            binding.historyList.addView(empty)
            return
        }

        captures.forEachIndexed { index, objectModel ->
            val file = File(objectModel.sourcePath)
            val note = objectModel.noteName() ?: objectModel.detectedPitchHz?.let {
                String.format("%.1f Hz", it)
            } ?: "pitch unknown"
            val kind = if (objectModel.transformation == null) "ORIGINAL" else "DERIVED · OCTAVE UP"
            val decision = objectModel.loopDecision?.uppercase()?.let { " · ${it}" } ?: ""
            val name = objectModel.displayName?.let { " · ${it}" } ?: ""
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(14.dp(), 10.dp(), 14.dp(), 10.dp())
                setBackgroundResource(R.drawable.bg_input)
            }

            val label = Button(this).apply {
                text = (index + 1).toString() + ". " + kind + decision + name + "\n" + note + " · " + String.format("%.2fs", objectModel.durationMs / 1000f)
                isAllCaps = false
                setOnClickListener {
                    if (!file.exists()) {
                        showStatus("Capture " + objectModel.id.take(8) + " is missing its audio file.")
                        return@setOnClickListener
                    }
                    lastCapture = file
                    selectedObject = objectModel
                    renderObject(file, objectModel)
                    showStatus("Selected " + kind.lowercase() + " " + objectModel.id.take(8) + ".")
                }
            }
            card.addView(label)

            val controls = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
            }
            val play = Button(this).apply {
                text = "PLAY"
                isAllCaps = false
                isEnabled = file.exists()
            }
            val pause = Button(this).apply {
                text = "PAUSE"
                isAllCaps = false
                isEnabled = false
            }
            val repeat = Button(this).apply {
                text = "REPEAT"
                isAllCaps = false
                isEnabled = file.exists()
            }
            play.setOnClickListener { playCapture(file, play, pause, repeat) }
            pause.setOnClickListener { pauseOrResume(file, play, pause, repeat) }
            repeat.setOnClickListener { toggleRepeat(file, play, pause, repeat) }

            controls.addView(play, LinearLayout.LayoutParams(0, 48.dp(), 1f))
            controls.addView(pause, LinearLayout.LayoutParams(0, 48.dp(), 1f))
            controls.addView(repeat, LinearLayout.LayoutParams(0, 48.dp(), 1f))
            card.addView(controls)

            val editControls = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
            val clone = Button(this).apply { text = "CLONE"; isAllCaps = false }
            val rename = Button(this).apply { text = "RENAME"; isAllCaps = false }
            val delete = Button(this).apply { text = "DELETE"; isAllCaps = false }
            clone.setOnClickListener { cloneCapture(objectModel) }
            rename.setOnClickListener { renameCapture(objectModel) }
            delete.setOnClickListener { deleteCapture(objectModel) }
            editControls.addView(clone, LinearLayout.LayoutParams(0, 44.dp(), 1f))
            editControls.addView(rename, LinearLayout.LayoutParams(0, 44.dp(), 1f))
            editControls.addView(delete, LinearLayout.LayoutParams(0, 44.dp(), 1f))
            card.addView(editControls)

            binding.historyList.addView(card, LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { bottomMargin = 10.dp() })
        }
    }

    private fun undoAction() {
        stopPlayback()
        if (sessionStore.undo()) {
            selectedObject = null
            lastCapture = null
            binding.objectCard.visibility = View.GONE
            renderHistory()
            showStatus("Undid the last object change.")
        }
    }

    private fun redoAction() {
        stopPlayback()
        if (sessionStore.redo()) {
            selectedObject = null
            lastCapture = null
            binding.objectCard.visibility = View.GONE
            renderHistory()
            showStatus("Redid the object change.")
        }
    }

    private fun cloneCapture(objectModel: MieMusicalObject) {
        val source = File(objectModel.sourcePath)
        if (!source.exists()) {
            showStatus("This capture's audio file is missing.")
            return
        }
        runCatching {
            val cloneId = java.util.UUID.randomUUID().toString()
            val output = File(source.parentFile, "mie-" + cloneId + "-clone.wav")
            source.copyTo(output)
            val clone = sessionStore.cloneCapture(objectModel, output.absolutePath)
            File(output.parentFile, clone.id + ".json").writeText(clone.toJson())
            selectedObject = clone
            lastCapture = output
            renderObject(output, clone)
            renderHistory()
            showStatus("Cloned " + objectModel.id.take(8) + " as " + clone.id.take(8) + ". The clone is independent.")
        }.onFailure { showStatus("Clone failed: " + (it.message ?: "unknown error")) }
    }

    private fun renameCapture(objectModel: MieMusicalObject) {
        val input = EditText(this).apply {
            setText(objectModel.displayName ?: "")
            hint = "Object name"
            setSingleLine(true)
        }
        AlertDialog.Builder(this)
            .setTitle("Rename musical object")
            .setView(input)
            .setNegativeButton("CANCEL", null)
            .setPositiveButton("SAVE") { _, _ ->
                val name = input.text?.toString()
                if (sessionStore.renameCapture(objectModel.id, name)) {
                    val updated = sessionStore.current().captures.firstOrNull { it.id == objectModel.id }
                    if (updated != null) {
                        selectedObject = updated
                        lastCapture = File(updated.sourcePath)
                        renderObject(lastCapture!!, updated)
                    }
                    renderHistory()
                    showStatus("Object renamed.")
                }
            }
            .show()
    }

    private fun deleteCapture(objectModel: MieMusicalObject) {
        if (sessionStore.deleteCapture(objectModel.id)) {
            if (selectedObject?.id == objectModel.id) {
                selectedObject = null
                lastCapture = null
                binding.objectCard.visibility = View.GONE
            }
            stopPlayback()
            renderHistory()
            showStatus("Moved " + objectModel.id.take(8) + " to trash. It can be restored.")
        }
    }

    private fun restoreCapture(objectModel: MieMusicalObject) {
        if (sessionStore.restoreCapture(objectModel.id)) {
            renderHistory()
            showStatus("Restored " + objectModel.id.take(8) + ".")
        }
    }

    private fun transformSelectedCapture() {
        val source = selectedObject
        val sourceFile = lastCapture
        if (source == null || sourceFile == null || !sourceFile.exists()) {
            showStatus("Select a saved capture before transforming it.")
            return
        }
        if (source.transformation != null) {
            showStatus("This capture is already a derived transformation. Select an original capture.")
            return
        }

        showStatus("Creating octave-up derivative…")
        Thread {
            runCatching {
                val output = File(sourceFile.parentFile, "mie-" + System.currentTimeMillis() + "-octave-up.wav")
                MieAudioTransformer.octaveUp(sourceFile, output)
                val derived = source.copy(
                    id = java.util.UUID.randomUUID().toString(),
                    sourcePath = output.absolutePath,
                    durationMs = recorder.durationMs(output),
                    parentId = source.id,
                    transformation = "octave_up"
                )
                File(output.parentFile, derived.id + ".json").writeText(derived.toJson())
                sessionStore.addCapture(derived)
                runOnUiThread {
                    renderObject(output, derived)
                    renderHistory()
                    showStatus("Created octave-up derivative " + derived.id.take(8) + " from " + source.id.take(8) + ". Original preserved.")
                }
            }.onFailure { error ->
                runOnUiThread { showStatus("Transformation failed: " + (error.message ?: "unknown error")) }
            }
        }.start()
    }

    private fun keepSelectedResult() {
        val selected = selectedObject
        if (selected == null || selected.transformation == null) {
            showStatus("Create a changed result before keeping it.")
            return
        }
        val kept = selected.copy(loopDecision = "kept")
        sessionStore.updateCapture(kept)
        selectedObject = kept
        lastCapture = File(kept.sourcePath)
        renderObject(lastCapture!!, kept)
        renderHistory()
        showStatus("Kept result ${kept.id.take(8)}. Original remains recoverable.")
    }

    private fun reviseSelectedResult() {
        val selected = selectedObject
        if (selected == null || selected.transformation == null || selected.parentId == null) {
            showStatus("Select a changed result to revise it.")
            return
        }
        val revised = selected.copy(loopDecision = "revised")
        sessionStore.updateCapture(revised)
        val parentId = revised.parentId ?: return
        val parent = sessionStore.current().captures.firstOrNull { it.id == parentId }
        if (parent == null) {
            showStatus("Original parent ${parentId.take(8)} is unavailable.")
            return
        }
        selectedObject = parent
        lastCapture = File(parent.sourcePath)
        renderObject(lastCapture!!, parent)
        renderHistory()
        showStatus("Result revised. Original restored for another change.")
    }

    private fun playCapture(file: File, play: Button, pause: Button, repeat: Button, preserveRepeat: Boolean = false) {
        if (!file.exists()) {
            showStatus("This capture's audio file is missing.")
            return
        }

        if (playingFile?.absolutePath == file.absolutePath && mediaPlayer != null) {
            mediaPlayer?.let { player ->
                if (!player.isPlaying) {
                    player.start()
                    pause.text = "PAUSE"
                    pause.isEnabled = true
                    play.text = "PLAYING"
                }
            }
            return
        }

        stopPlayback(resetRepeat = !preserveRepeat)
        playingFile = file
        playingButton = play
        pauseButton = pause
        repeatButton = repeat

        mediaPlayer = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            setOnCompletionListener {
                if (repeatPlayback && playingFile?.absolutePath == file.absolutePath) {
                    seekTo(0)
                    start()
                } else {
                    stopPlayback()
                }
            }
            setOnErrorListener { _, _, _ ->
                showStatus("Playback failed for this capture.")
                stopPlayback()
                true
            }
            prepare()
            start()
        }
        play.text = "PLAYING"
        pause.isEnabled = true
        repeat.isEnabled = true
        showStatus("Playing " + file.name + ".")
    }

    private fun pauseOrResume(file: File, play: Button, pause: Button, repeat: Button) {
        if (playingFile?.absolutePath != file.absolutePath || mediaPlayer == null) {
            playCapture(file, play, pause, repeat)
            return
        }
        mediaPlayer?.let { player ->
            if (player.isPlaying) {
                player.pause()
                pause.text = "RESUME"
                play.text = "PLAY"
                showStatus("Paused " + file.name + ".")
            } else {
                player.start()
                pause.text = "PAUSE"
                play.text = "PLAYING"
                showStatus("Resumed " + file.name + ".")
            }
        }
    }

    private fun toggleRepeat(file: File, play: Button, pause: Button, repeat: Button) {
        if (playingFile?.absolutePath != file.absolutePath || mediaPlayer == null) {
            repeatPlayback = true
            repeat.text = "REPEAT ✓"
            playCapture(file, play, pause, repeat, preserveRepeat = true)
            return
        }
        repeatPlayback = !repeatPlayback
        repeat.text = if (repeatPlayback) "REPEAT ✓" else "REPEAT"
        showStatus(if (repeatPlayback) "Repeat enabled." else "Repeat disabled.")
    }

    private fun stopPlayback(resetRepeat: Boolean = true) {
        mediaPlayer?.let {
            runCatching { if (it.isPlaying) it.stop() }
            it.release()
        }
        mediaPlayer = null
        playingFile = null
        playingButton?.text = "PLAY"
        pauseButton?.text = "PAUSE"
        pauseButton?.isEnabled = false
        repeatButton?.text = "REPEAT"
        playingButton = null
        pauseButton = null
        repeatButton = null
        if (resetRepeat) repeatPlayback = false
    }

    private fun Int.dp(): Int = (this * resources.displayMetrics.density).roundToInt()

    private fun showStatus(message: String) {
        runOnUiThread { binding.status.text = message }
    }

    override fun onStop() {
        super.onStop()
        stopPlayback()
        if (recorder.isRecording()) recorder.stop()
    }
}
