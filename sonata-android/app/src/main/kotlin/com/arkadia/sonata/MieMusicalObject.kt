package com.arkadia.sonata

import org.json.JSONObject
import java.util.UUID

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
    val parentId: String? = null
) {
    fun toJson(): String {
        val interpretation = JSONObject()
            .put("type", inputType)
            .put("confidence", confidence.toDouble())
            .put("rms", rms.toDouble())
            .put("zero_crossing_rate", zeroCrossingRate.toDouble())
            .put("detected_pitch_hz", detectedPitchHz)
            .put("detected_midi", detectedMidi)

        return JSONObject()
            .put("id", id)
            .put("source", sourcePath)
            .put("duration_ms", durationMs)
            .put("interpretation", interpretation)
            .put(
                "provenance",
                JSONObject()
                    .put("parent_id", parentId)
                    .put("created_at_epoch_ms", createdAtEpochMs)
            )
            .toString(2)
    }
}
