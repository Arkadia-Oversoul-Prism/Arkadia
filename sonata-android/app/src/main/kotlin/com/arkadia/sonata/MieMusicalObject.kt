package com.arkadia.sonata

import org.json.JSONObject
import java.util.UUID
import kotlin.math.roundToInt

data class MieMusicalObject(
    val id: String = UUID.randomUUID().toString(),
    val sourcePath: String,
    val durationMs: Long,
    val inputType: String,
    val confidence: Float,
    val rms: Float,
    val zeroCrossingRate: Float,
    val detectedPitchHz: Float?,
    val detectedMidi: Float?,
    val createdAtEpochMs: Long = System.currentTimeMillis(),
    val parentId: String? = null,
    val transformation: String? = null,
    val loopDecision: String? = null
) {
    fun noteName(): String? {
        val midi = detectedMidi ?: return null
        if (!midi.isFinite()) return null
        val rounded = midi.roundToInt()
        if (rounded !in 0..127) return null
        val names = arrayOf("C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B")
        return names[rounded % 12] + (rounded / 12 - 1)
    }

    fun humanType(): String = when (inputType) {
        "melody_candidate" -> "Melody candidate"
        "rhythm_or_percussive_candidate" -> "Percussive candidate"
        else -> "Uncertain musical input"
    }

    fun toJson(): String {
        val interpretation = JSONObject()
            .put("type", inputType)
            .put("confidence", confidence.toDouble())
            .put("rms", rms.toDouble())
            .put("zero_crossing_rate", zeroCrossingRate.toDouble())
            .put("detected_pitch_hz", detectedPitchHz)
            .put("detected_midi", detectedMidi)

        val provenance = JSONObject()
            .put("parent_id", parentId)
            .put("transformation", transformation)
            .put("created_at_epoch_ms", createdAtEpochMs)
        if (loopDecision != null) {
            provenance.put("loop_decision", loopDecision)
        }

        return JSONObject()
            .put("id", id)
            .put("source", sourcePath)
            .put("duration_ms", durationMs)
            .put("interpretation", interpretation)
            .put("provenance", provenance)
            .toString(2)
    }
}
