package com.arkadia.sonata

import java.io.File
import java.io.FileInputStream
import kotlin.math.log2
import kotlin.math.max
import kotlin.math.sqrt

data class MieInterpretation(
    val inputType: String,
    val confidence: Float,
    val rms: Float,
    val zeroCrossingRate: Float,
    val pitchHz: Float?
) {
    val midi: Float?
        get() = pitchHz?.takeIf { it > 0f }?.let { 69f + 12f * log2(it / 440f) }
}

object MieMusicalInterpreter {
    private const val SAMPLE_RATE = 16_000
    private const val FRAME = 2048
    private const val MIN_LAG = 16
    private const val MAX_LAG = 800
    private const val PEAK_RATIO = 0.85f

    fun interpret(file: File): MieInterpretation {
        val samples = readPcm16(file)
        if (samples.isEmpty()) return MieInterpretation("ambiguous", 0f, 0f, 0f, null)

        val rms = sqrt(samples.map { it * it }.average().toFloat()).coerceAtLeast(0f)
        val zcr = zeroCrossingRate(samples)

        val pitches = mutableListOf<Float>()
        val confidences = mutableListOf<Float>()
        val step = FRAME / 2
        var offset = 0
        while (offset + FRAME <= samples.size && pitches.size < 8) {
            val estimate = estimatePitch(samples.copyOfRange(offset, offset + FRAME))
            if (estimate != null) {
                pitches += estimate.first
                confidences += estimate.second
            }
            offset += step
        }

        val pitch = pitches.takeIf { it.size >= 2 }?.sorted()?.let { it[it.size / 2] }
        val pitchConfidence = if (confidences.isEmpty()) 0f else confidences.average().toFloat()
        val possibleFrames = max(1, minOf(8, ((samples.size - FRAME).coerceAtLeast(0) / step) + 1))
        val voicedRatio = pitches.size / possibleFrames.toFloat()

        val type = when {
            pitch != null && voicedRatio >= 0.35f && pitchConfidence >= 0.45f -> "melody_candidate"
            rms > 0.025f && zcr >= 0.035f -> "rhythm_or_percussive_candidate"
            else -> "ambiguous"
        }
        val confidence = when (type) {
            "melody_candidate" -> (0.55f * pitchConfidence + 0.45f * voicedRatio).coerceIn(0f, 1f)
            "rhythm_or_percussive_candidate" ->
                (0.35f + (zcr.coerceAtMost(0.2f) / 0.2f) * 0.45f).coerceIn(0f, 0.8f)
            else -> 0.25f
        }

        return MieInterpretation(type, confidence, rms, zcr, pitch)
    }

    private fun readPcm16(file: File): FloatArray {
        val bytes = FileInputStream(file).use { input ->
            input.skip(44L)
            input.readBytes()
        }
        val count = bytes.size / 2
        return FloatArray(count) { i ->
            val lo = bytes[i * 2].toInt() and 0xff
            val hi = bytes[i * 2 + 1].toInt()
            ((hi shl 8) or lo).toShort() / 32768f
        }
    }

    private fun zeroCrossingRate(samples: FloatArray): Float {
        if (samples.size < 2) return 0f
        var crossings = 0
        for (i in 1 until samples.size) {
            if ((samples[i - 1] >= 0f) != (samples[i] >= 0f)) crossings++
        }
        return crossings.toFloat() / (samples.size - 1)
    }

    private fun estimatePitch(frame: FloatArray): Pair<Float, Float>? {
        val energy = sqrt(frame.map { it * it }.average().toFloat())
        if (energy < 0.015f) return null

        val minLag = max(MIN_LAG, SAMPLE_RATE / 1000)
        val maxLag = minOf(MAX_LAG, SAMPLE_RATE / 55)
        val correlations = FloatArray(maxLag + 2)

        for (lag in minLag..maxLag) {
            var dot = 0.0
            var a = 0.0
            var b = 0.0
            var i = 0
            while (i + lag < frame.size) {
                val x = frame[i].toDouble()
                val y = frame[i + lag].toDouble()
                dot += x * y
                a += x * x
                b += y * y
                i++
            }
            correlations[lag] = if (a > 0 && b > 0) (dot / sqrt(a * b)).toFloat() else -1f
        }

        val peak = (minLag..maxLag).maxOf { correlations[it] }
        if (peak < 0.35f) return null

        // A periodic signal correlates strongly at every multiple of its period, so the global
        // maximum is often a subharmonic (a 440 Hz tone peaks at lag 109 = 3 periods). Take the
        // first local maximum within PEAK_RATIO of the peak instead: the smallest lag that nearly
        // matches is the true fundamental.
        val threshold = peak * PEAK_RATIO
        for (lag in minLag..maxLag) {
            if (correlations[lag] < threshold) continue
            if (correlations[lag] < correlations[lag - 1]) continue
            if (correlations[lag] < correlations[lag + 1]) continue
            val left = correlations[lag - 1]
            val right = correlations[lag + 1]
            val denominator = left - 2f * correlations[lag] + right
            val delta = if (denominator != 0f) {
                (0.5f * (left - right) / denominator).coerceIn(-0.5f, 0.5f)
            } else {
                0f
            }
            return (SAMPLE_RATE.toFloat() / (lag + delta)) to correlations[lag]
        }
        return null
    }
}
