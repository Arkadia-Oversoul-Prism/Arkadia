package com.arkadia.os

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.media.MediaRecorder
import android.os.Bundle
import android.view.Gravity
import android.widget.*
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import java.io.File
import java.util.UUID

class MainActivity : AppCompatActivity() {
    private lateinit var prefs: Prefs
    private lateinit var api: ConsoleApi
    private lateinit var content: LinearLayout
    private var recorder: MediaRecorder? = null
    private var recordingFile: File? = null

    private val bg = Color.rgb(8, 10, 15)
    private val card = Color.rgb(18, 21, 30)
    private val text = Color.rgb(232, 236, 240)
    private val muted = Color.rgb(132, 143, 153)
    private val accent = Color.rgb(0, 212, 170)
    private val gold = Color.rgb(201, 168, 76)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = Prefs(this)
        api = ConsoleApi(prefs)
        buildShell()
        refresh()
    }

    private fun buildShell() {
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(bg) }
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(20), dp(18), dp(12), dp(10))
        }
        header.addView(label("SOLARIUN", 18f, gold, true), LinearLayout.LayoutParams(0, -2, 1f))
        header.addView(button("ARKANA") { ask() })
        header.addView(button("CAPTURE") { captureNote() })
        header.addView(button("⚙") { startActivity(Intent(this, SettingsActivity::class.java)) })
        root.addView(header)
        val scroll = ScrollView(this)
        content = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(16), 0, dp(16), dp(32)) }
        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        val nav = LinearLayout(this).apply { gravity = Gravity.CENTER; setPadding(dp(10), dp(8), dp(10), dp(10)) }
        nav.addView(navButton("FIELD", true) { refresh() })
        nav.addView(navButton("WORK", false) { toast("WORK reads the same canonical workload surface.") })
        nav.addView(navButton("VERIFY", false) { toast("VERIFY reads the WorkEvent evidence spine.") })
        root.addView(nav)
        setContentView(root)
    }

    private fun refresh() {
        content.removeAllViews()
        content.addView(label("YOUR LIVING FIELD", 11f, accent, true))
        content.addView(label("Reading canonical SolSpire state. This console is a lens, not another source of truth.", 14f, muted, false), margin(0, 4, 0, 18))
        content.addView(label("READING…", 12f, muted, false))
        lifecycleScope.launch {
            runCatching { api.snapshot() }.onSuccess { s ->
                content.removeAllViews()
                content.addView(label("YOUR LIVING FIELD", 11f, accent, true))
                content.addView(label("CAN ≠ MAY ≠ DID", 12f, muted, true), margin(0, 4, 0, 16))
                s.workspace?.let { addObject("WORLD", it.optString("display_name", "Solariun Workspace"), it.optString("lifecycle", "UNKNOWN"), it.optString("subject_binding", "canonical")) }
                s.pulse?.let { addObject("SIGNAL", it.optString("current_signal", it.optString("signal_summary", "No current signal")), it.optString("period", "today"), it.optString("state_summary", "UNKNOWN")) }
                s.workload?.let { addObject("WORK", it.optString("title", it.optString("display_name", "Current workload")), it.optString("status", "UNKNOWN"), it.optString("objective", "UNKNOWN")) }
                s.synthesis?.let { addObject("KNOWLEDGE", "Current synthesis", "LIVE", it.optString("summary", it.optString("synthesis_summary", "UNKNOWN"))) }
                s.proposals.take(5).forEach { addProposal(it) }
                if (s.events.isNotEmpty()) addObject("EVIDENCE", "Recent WorkEvents", "${s.events.size} observed", "Canonical event spine")
                content.addView(label("FIELD STATUS", 10f, accent, true), margin(0, 22, 0, 6))
                content.addView(label("Display does not authorize execution. Human authorization remains the consequential boundary.", 12f, muted, false))
            }.onFailure {
                content.removeAllViews()
                content.addView(label("FIELD UNAVAILABLE", 12f, gold, true))
                content.addView(label(it.message ?: "Unable to reach the canonical API.", 13f, muted, false), margin(0, 8, 0, 16))
                content.addView(button("RETRY") { refresh() })
                content.addView(label("Authentication is required for protected SolSpire routes. Configure a bearer ID token in Console settings for this first native slice.", 12f, muted, false), margin(0, 14, 0, 0))
            }
        }
    }

    private fun addObject(type: String, title: String, status: String, summary: String) {
        val box = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(16), dp(14), dp(16), dp(14)); setBackgroundColor(card) }
        box.addView(label(type, 10f, accent, true))
        box.addView(label(title.ifBlank { "UNKNOWN" }, 19f, text, true), margin(0, 5, 0, 3))
        box.addView(label(status.ifBlank { "UNKNOWN" }, 10f, gold, true))
        box.addView(label(summary.ifBlank { "UNKNOWN" }, 13f, muted, false), margin(0, 8, 0, 0))
        content.addView(box, margin(0, 0, 0, 10))
    }

    private fun addProposal(p: org.json.JSONObject) {
        val id = p.optString("proposal_id")
        val status = p.optString("proposal_status", p.optString("status", "UNKNOWN"))
        addObject("PROPOSAL", p.optString("objective", "Untitled proposal"), status, p.optString("requested_decision", "Review required"))
        if (id.isNotBlank() && status.uppercase() in setOf("PROPOSED", "PENDING", "UNDER_REVIEW")) {
            val row = LinearLayout(this).apply { gravity = Gravity.END }
            row.addView(button("DECLINE") { decide(id, "DECLINED") })
            row.addView(button("ACCEPT") { decide(id, "ACCEPTED") })
            content.addView(row, margin(0, -4, 0, 10))
        }
    }

    private fun decide(id: String, decision: String) {
        lifecycleScope.launch {
            runCatching { api.decide(id, decision) }
                .onSuccess { toast("Decision recorded: $decision. This does not prove execution.") }
                .onFailure { toast(it.message ?: "Decision failed") }
            refresh()
        }
    }

    private fun ask() {
        val input = EditText(this).apply { hint = "Ask Arkana…"; setTextColor(this@MainActivity.text); setHintTextColor(muted); minLines = 3 }
        AlertDialog.Builder(this).setTitle("ARKANA").setMessage("Interrogate the intelligence layer. Where evidence stops, the claim stops.")
            .setView(input).setNegativeButton("CLOSE", null).setPositiveButton("ASK") { _, _ ->
                val q = input.text.toString().trim()
                if (q.isNotBlank()) lifecycleScope.launch {
                    toast("Asking Arkana…")
                    runCatching { api.askArkana(q) }.onSuccess { showResponse(it) }.onFailure { toast(it.message ?: "Arkana unavailable") }
                }
            }.show()
    }

    private fun showResponse(reply: String) {
        AlertDialog.Builder(this).setTitle("ARKANA / RESPONSE").setMessage(reply).setPositiveButton("CLOSE", null).show()
    }

    private fun captureNote() {
        val input = EditText(this).apply { hint = "What happened?"; setTextColor(text); setHintTextColor(muted); minLines = 4 }
        AlertDialog.Builder(this).setTitle("CAPTURE REALITY").setMessage("Capture first. Interpretation can follow.")
            .setView(input).setNegativeButton("CLOSE", null).setPositiveButton("RECORD") { _, _ ->
                val note = input.text.toString().trim()
                if (note.isNotBlank()) lifecycleScope.launch {
                    runCatching { api.emitCapture("Mobile observation", note) }
                        .onSuccess { toast("Captured into the WorkEvent spine.") }
                        .onFailure { toast(it.message ?: "Capture failed") }
                }
            }.setNeutralButton("AUDIO") { _, _ -> startAudioCapture() }.show()
    }

    private fun startAudioCapture() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.RECORD_AUDIO), 41)
            toast("Microphone permission required. Tap CAPTURE → AUDIO again after granting it.")
            return
        }
        val file = File(filesDir, "captures").apply { mkdirs() }.resolve("capture-${UUID.randomUUID()}.m4a")
        recordingFile = file
        recorder = MediaRecorder(this).apply {
            setAudioSource(MediaRecorder.AudioSource.MIC); setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC); setOutputFile(file.absolutePath); prepare(); start()
        }
        AlertDialog.Builder(this).setTitle("CAPTURING REALITY")
            .setMessage("Raw audio is being preserved locally. Stop when the observation is complete.")
            .setPositiveButton("STOP") { _, _ ->
                recorder?.runCatching { stop() }; recorder?.release(); recorder = null
                lifecycleScope.launch {
                    runCatching { api.emitCapture("Audio capture", "Local raw audio capture", recordingFile?.name) }
                        .onSuccess { toast("Audio preserved: ${recordingFile?.name}") }
                        .onFailure { toast("Audio saved locally; event recording failed.") }
                }
            }.setOnCancelListener { recorder?.runCatching { stop() }; recorder?.release(); recorder = null }.show()
    }

    private fun navButton(title: String, active: Boolean, action: () -> Unit) = button(title) { action() }.apply { alpha = if (active) 1f else 0.65f }
    private fun button(title: String, action: () -> Unit) = Button(this).apply { text = title; textSize = 10f; setTextColor(if (title == "ACCEPT") accent else this@MainActivity.text); setOnClickListener { action() } }
    private fun label(value: String, size: Float, color: Int, bold: Boolean) = TextView(this).apply { text = value; textSize = size; setTextColor(color); typeface = Typeface.create(Typeface.MONOSPACE, if (bold) Typeface.BOLD else Typeface.NORMAL) }
    private fun margin(l: Int, t: Int, r: Int, b: Int) = LinearLayout.LayoutParams(-1, -2).apply { setMargins(dp(l), dp(t), dp(r), dp(b)) }
    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
    private fun toast(s: String) = Toast.makeText(this, s, Toast.LENGTH_SHORT).show()
}
