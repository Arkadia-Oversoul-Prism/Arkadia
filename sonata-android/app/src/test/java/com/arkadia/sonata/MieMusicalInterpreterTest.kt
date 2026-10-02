package com.arkadia.sonata

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.io.FileOutputStream
import kotlin.math.PI
import kotlin.math.sin

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

    private fun writeMonoPcmWav(file: File, sampleRate: Int, frequencyHz: Float, durationMs: Int) {
        val sampleCount = sampleRate * durationMs / 1000
        val pcm = ByteArray(sampleCount * 2)
        for (i in 0 until sampleCount) {
            val sample = (sin(2.0 * PI * frequencyHz * i / sampleRate) * 0.45 * 32767.0).toInt()
            pcm[i * 2] = (sample and 0xff).toByte()
            pcm[i * 2 + 1] = ((sample shr 8) and 0xff).toByte()
        }

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
