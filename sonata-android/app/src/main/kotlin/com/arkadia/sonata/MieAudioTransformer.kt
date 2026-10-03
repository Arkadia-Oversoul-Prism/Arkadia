package com.arkadia.sonata

import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import kotlin.math.roundToInt

object MieAudioTransformer {
    private const val HEADER_SIZE = 44

    /**
     * Smallest reversible musical transformation: transpose the remembered PCM
     * capture up one octave by resampling at 2x. The original WAV is untouched.
     * Duration changes with the pitch because this is intentionally a first
     * transformation proof, not a full time-preserving pitch shifter.
     */
    fun octaveUp(source: File, output: File) {
        val bytes = FileInputStream(source).use { input ->
            input.skip(HEADER_SIZE.toLong())
            input.readBytes()
        }
        require(bytes.size >= 2) { "Source contains no PCM audio" }

        val sourceSamples = bytes.size / 2
        val targetSamples = (sourceSamples / 2).coerceAtLeast(1)
        val pcm = ByteArray(targetSamples * 2)

        for (i in 0 until targetSamples) {
            val sourceIndex = i * 2
            val sample = readSample(bytes, sourceIndex)
            writeSample(pcm, i, sample)
        }

        writeWav(output, pcm)
    }

    private fun readSample(bytes: ByteArray, sampleIndex: Int): Short {
        val offset = sampleIndex * 2
        val lo = bytes[offset].toInt() and 0xff
        val hi = bytes[offset + 1].toInt()
        return ((hi shl 8) or lo).toShort()
    }

    private fun writeSample(bytes: ByteArray, sampleIndex: Int, sample: Short) {
        val offset = sampleIndex * 2
        bytes[offset] = (sample.toInt() and 0xff).toByte()
        bytes[offset + 1] = (sample.toInt() shr 8).toByte()
    }

    private fun writeWav(file: File, pcm: ByteArray) {
        FileOutputStream(file).use { out ->
            val sampleRate = 16_000
            val channels = 1
            val bitsPerSample = 16
            val byteRate = sampleRate * channels * bitsPerSample / 8
            val blockAlign = channels * bitsPerSample / 8
            val dataLength = pcm.size

            out.write("RIFF".toByteArray(Charsets.US_ASCII))
            writeIntLE(out, 36 + dataLength)
            out.write("WAVE".toByteArray(Charsets.US_ASCII))
            out.write("fmt ".toByteArray(Charsets.US_ASCII))
            writeIntLE(out, 16)
            writeShortLE(out, 1)
            writeShortLE(out, channels)
            writeIntLE(out, sampleRate)
            writeIntLE(out, byteRate)
            writeShortLE(out, blockAlign)
            writeShortLE(out, bitsPerSample)
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
