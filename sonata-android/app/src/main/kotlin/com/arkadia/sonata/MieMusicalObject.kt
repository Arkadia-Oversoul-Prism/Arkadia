package com.arkadia.sonata

import java.util.Locale
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
        fun esc(value: String): String =
            value.replace("\\", "\\\\").replace("\"", "\\\"")
        val pitch = detectedPitchHz?.let { String.format(Locale.US, "%.2f", it) } ?: "null"
        val midi = detectedMidi?.let { String.format(Locale.US, "%.2f", it) } ?: "null"
        val parent = parentId?.let { "\"" + esc(it) + "\"" } ?: "null"
        return "{\n" +
            "  \"id\":\"" + esc(id) + "\",\n" +
            "  \"source\":\"" + esc(sourcePath) + "\",\n" +
            "  \"duration_ms\":" + durationMs + ",\n" +
            "  \"interpretation\":{\n" +
            "    \"type\":\"" + esc(inputType) + "\",\n" +
            "    \"confidence\":" + String.format(Locale.US, "%.3f", confidence) + ",\n" +
            "    \"rms\":" + String.format(Locale.US, "%.5f", rms) + ",\n" +
            "    \"zero_crossing_rate\":" + String.format(Locale.US, "%.5f", zeroCrossingRate) + ",\n" +
            "    \"detected_pitch_hz\":" + pitch + ",\n" +
            "    \"detected_midi\":" + midi + "\n" +
            "  },\n" +
            "  \"provenance\":{\n" +
            "    \"parent_id\":" + parent + ",\n" +
            "    \"created_at_epoch_ms\":" + createdAtEpochMs + "\n" +
            "  }\n" +
            "}"
    }
}
