package com.arkadia.sonata

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.io.FileOutputStream
import kotlin.math.PI
import kotlin.math.sin
import kotlin.random.Random

class MieMusicalInterpreterTest {
    @Test
    fun sustained440HzToneProducesMelodyCandidate() {
        val file = File.createTempFile("mie-test-", ".wav")
        try {
            writeMonoPcmWav(file, sampleRate = 16_000, frequencyHz = 440f, durationMs = 1500)
            val result = MieMusicalInterpreter.interpret(file)

            assertEquals("melody_candidate", result.inputType)
            assertNotNull(result.pitchHz)
            assertTrue(result.pitchHz!! in 430f..450f)
            assertTrue(result.confidence >= 0.45f)
        } finally {
            file.delete()
        }
    }

    /**
     * Regression for the subharmonic error: autocorrelation peaks at every multiple of the
     * period, so a naive global-maximum search reported 146.8 Hz (3 periods of 440 Hz) and
     * failed [sustained440HzToneProducesMelodyCandidate]. Lower tones failed the same way.
     */
    @Test
    fun lowerTonesAreNotReportedAsSubharmonics() {
        for (expected in listOf(110f, 220f, 440f, 880f)) {
            val file = File.createTempFile("mie-test-", ".wav")
            try {
                writeMonoPcmWav(file, sampleRate = 16_000, frequencyHz = expected, durationMs = 1500)
                val result = MieMusicalInterpreter.interpret(file)
                val detected = result.pitchHz
                assertNotNull("expected a pitch for $expected Hz", detected)
                assertTrue(
                    "expected ~$expected Hz, got $detected",
                    detected!! in (expected * 0.97f)..(expected * 1.03f)
                )
            } finally {
                file.delete()
            }
        }
    }

    /** Negative control: noise must not be reported as a melody candidate. */
    @Test
    fun broadbandNoiseIsNotAMelodyCandidate() {
        val file = File.createTempFile("mie-test-", ".wav")
        try {
            writeNoiseWav(file, sampleRate = 16_000, durationMs = 1500)
            val result = MieMusicalInterpreter.interpret(file)

            assertTrue("expected non-melodic classification, got ${result.inputType}", result.inputType != "melody_candidate")
        } finally {
            file.delete()
        }
    }

    private fun writeNoiseWav(file: File, sampleRate: Int, durationMs: Int) {
        val random = Random(7)
        val sampleCount = sampleRate * durationMs / 1000
        val pcm = ByteArray(sampleCount * 2)
        for (i in 0 until sampleCount) {
            val sample = ((random.nextFloat() * 2f - 1f) * 0.4f * 32767f).toInt()
            pcm[i * 2] = (sample and 0xff).toByte()
            pcm[i * 2 + 1] = ((sample shr 8) and 0xff).toByte()
        }
        writeWav(file, sampleRate, pcm)
    }

    private fun writeMonoPcmWav(file: File, sampleRate: Int, frequencyHz: Float, durationMs: Int) {
        val sampleCount = sampleRate * durationMs / 1000
        val pcm = ByteArray(sampleCount * 2)
        for (i in 0 until sampleCount) {
            val sample = (sin(2.0 * PI * frequencyHz * i / sampleRate) * 0.45 * 32767.0).toInt()
            pcm[i * 2] = (sample and 0xff).toByte()
            pcm[i * 2 + 1] = ((sample shr 8) and 0xff).toByte()
        }

        writeWav(file, sampleRate, pcm)
    }

    private fun writeWav(file: File, sampleRate: Int, pcm: ByteArray) {
        FileOutputStream(file).use { out ->
            val dataLength = pcm.size
            val byteRate = sampleRate * 2
            out.write("RIFF".toByteArray(Charsets.US_ASCII))
            writeIntLE(out, 36 + dataLength)
            out.write("WAVE".toByteArray(Charsets.US_ASCII))
            out.write("fmt ".toByteArray(Charsets.US_ASCII))
            writeIntLE(out, 16)
            writeShortLE(out, 1)
            writeShortLE(out, 1)
            writeIntLE(out, sampleRate)
            writeIntLE(out, byteRate)
            writeShortLE(out, 2)
            writeShortLE(out, 16)
            out.write("data".toByteArray(Charsets.US_ASCII))
            writeIntLE(out, dataLength)
            out.write(pcm)
        }
    }

    private fun writeIntLE(out: FileOutputStream, value: Int) {
        out.write(value and 0xff)
        out.write((value shr 8) and 0xff)
        out.write((value shr 16) and 0xff)
        out.write((value shr 24) and 0xff)
    }

    private fun writeShortLE(out: FileOutputStream, value: Int) {
        out.write(value and 0xff)
        out.write((value shr 8) and 0xff)
    }
}
