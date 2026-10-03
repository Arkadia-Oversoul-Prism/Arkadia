package com.arkadia.sonata

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.UUID

data class MieSession(
    val id: String,
    val createdAtEpochMs: Long,
    val captures: MutableList<MieMusicalObject>
)

class MieSessionStore(context: Context) {
    private val root = File(context.filesDir, "mie")
    private val sessionFile = File(root, "session.json")
    private var session: MieSession

    init {
        root.mkdirs()
        session = load()
    }

    fun current(): MieSession = session

    fun addCapture(objectModel: MieMusicalObject) {
        session.captures.add(0, objectModel)
        save()
    }

    fun updateCapture(objectModel: MieMusicalObject) {
        val index = session.captures.indexOfFirst { it.id == objectModel.id }
        if (index >= 0) {
            session.captures[index] = objectModel
            save()
        }
    }

    fun save() {
        val captures = JSONArray()
        session.captures.forEach { captures.put(JSONObject(it.toJson())) }
        sessionFile.writeText(
            JSONObject()
                .put("session_id", session.id)
                .put("created_at_epoch_ms", session.createdAtEpochMs)
                .put("captures", captures)
                .toString(2)
        )
    }

    private fun load(): MieSession {
        if (!sessionFile.exists()) {
            return MieSession(UUID.randomUUID().toString(), System.currentTimeMillis(), mutableListOf())
        }
        return runCatching {
            val rootObject = JSONObject(sessionFile.readText())
            val capturesJson = rootObject.optJSONArray("captures") ?: JSONArray()
            val captures = mutableListOf<MieMusicalObject>()
            for (i in 0 until capturesJson.length()) {
                val item = capturesJson.getJSONObject(i)
                val interpretation = item.optJSONObject("interpretation") ?: JSONObject()
                val provenance = item.optJSONObject("provenance") ?: JSONObject()
                captures += MieMusicalObject(
                    id = item.optString("id"),
                    sourcePath = item.optString("source"),
                    durationMs = item.optLong("duration_ms"),
                    inputType = interpretation.optString("type", "ambiguous"),
                    confidence = interpretation.optDouble("confidence", 0.0).toFloat(),
                    rms = interpretation.optDouble("rms", 0.0).toFloat(),
                    zeroCrossingRate = interpretation.optDouble("zero_crossing_rate", 0.0).toFloat(),
                    detectedPitchHz = interpretation.optDouble("detected_pitch_hz", Double.NaN).let { if (it.isNaN()) null else it.toFloat() },
                    detectedMidi = interpretation.optDouble("detected_midi", Double.NaN).let { if (it.isNaN()) null else it.toFloat() },
                    createdAtEpochMs = provenance.optLong("created_at_epoch_ms", System.currentTimeMillis()),
                    parentId = provenance.optString("parent_id").takeIf { it.isNotBlank() && it != "null" },
                    transformation = provenance.optString("transformation").takeIf { it.isNotBlank() && it != "null" },
                    loopDecision = provenance.optString("loop_decision").takeIf { it.isNotBlank() && it != "null" }
                )
            }
            MieSession(
                id = rootObject.optString("session_id", UUID.randomUUID().toString()),
                createdAtEpochMs = rootObject.optLong("created_at_epoch_ms", System.currentTimeMillis()),
                captures = captures
            )
        }.getOrElse {
            MieSession(UUID.randomUUID().toString(), System.currentTimeMillis(), mutableListOf())
        }
    }
}
