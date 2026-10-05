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
    private val undoStack = mutableListOf<List<MieMusicalObject>>()
    private val redoStack = mutableListOf<List<MieMusicalObject>>()
    private val root = File(context.filesDir, "mie")
    private val sessionFile = File(root, "session.json")
    private var session: MieSession

    init {
        root.mkdirs()
        session = load()
    }

    fun current(): MieSession = session

    fun activeCaptures(): List<MieMusicalObject> = session.captures.filter { it.deletedAtEpochMs == null }

    fun deletedCaptures(): List<MieMusicalObject> = session.captures.filter { it.deletedAtEpochMs != null }

    fun canUndo(): Boolean = undoStack.isNotEmpty()
    fun canRedo(): Boolean = redoStack.isNotEmpty()

    private fun checkpoint() {
        undoStack.add(session.captures.map { it.copy() })
        if (undoStack.size > 50) undoStack.removeAt(0)
        redoStack.clear()
    }

    private fun replaceCaptures(next: List<MieMusicalObject>) {
        session.captures.clear()
        session.captures.addAll(next)
        save()
    }

    fun undo(): Boolean {
        if (undoStack.isEmpty()) return false
        redoStack.add(session.captures.map { it.copy() })
        replaceCaptures(undoStack.removeAt(undoStack.lastIndex))
        return true
    }

    fun redo(): Boolean {
        if (redoStack.isEmpty()) return false
        undoStack.add(session.captures.map { it.copy() })
        replaceCaptures(redoStack.removeAt(redoStack.lastIndex))
        return true
    }

    fun deleteCapture(id: String): Boolean {
        val index = session.captures.indexOfFirst { it.id == id && it.deletedAtEpochMs == null }
        if (index < 0) return false
        checkpoint()
        session.captures[index] = session.captures[index].copy(deletedAtEpochMs = System.currentTimeMillis())
        save()
        return true
    }

    fun restoreCapture(id: String): Boolean {
        val index = session.captures.indexOfFirst { it.id == id && it.deletedAtEpochMs != null }
        if (index < 0) return false
        checkpoint()
        session.captures[index] = session.captures[index].copy(deletedAtEpochMs = null)
        save()
        return true
    }

    fun cloneCapture(objectModel: MieMusicalObject, clonedSourcePath: String): MieMusicalObject {
        checkpoint()
        val clone = objectModel.copy(
            id = UUID.randomUUID().toString(),
            sourcePath = clonedSourcePath,
            createdAtEpochMs = System.currentTimeMillis(),
            parentId = null,
            transformation = null,
            loopDecision = null,
            displayName = objectModel.displayName?.let { "$it copy" },
            clonedFromId = objectModel.id,
            deletedAtEpochMs = null
        )
        session.captures.add(0, clone)
        save()
        return clone
    }

    fun renameCapture(id: String, name: String?): Boolean {
        val index = session.captures.indexOfFirst { it.id == id && it.deletedAtEpochMs == null }
        if (index < 0) return false
        checkpoint()
        session.captures[index] = session.captures[index].copy(displayName = name?.trim()?.takeIf { it.isNotEmpty() })
        save()
        return true
    }

    fun addCapture(objectModel: MieMusicalObject) {
        checkpoint()
        session.captures.add(0, objectModel)
        save()
    }

    fun updateCapture(objectModel: MieMusicalObject) {
        val index = session.captures.indexOfFirst { it.id == objectModel.id }
        if (index >= 0) {
            checkpoint()
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
                    loopDecision = provenance.optString("loop_decision").takeIf { it.isNotBlank() && it != "null" },
                    displayName = provenance.optString("display_name").takeIf { it.isNotBlank() && it != "null" },
                    clonedFromId = provenance.optString("cloned_from_id").takeIf { it.isNotBlank() && it != "null" },
                    deletedAtEpochMs = provenance.optLong("deleted_at_epoch_ms", Long.MIN_VALUE).let { if (it == Long.MIN_VALUE) null else it }
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
