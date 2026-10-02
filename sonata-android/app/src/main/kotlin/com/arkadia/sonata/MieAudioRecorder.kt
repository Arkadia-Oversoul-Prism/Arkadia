package com.arkadia.sonata

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream

class MieAudioRecorder(
    private val outputDir: File,
    private val sampleRate: Int = 16_000,
    private val maxDurationMs: Long = 10_000L
) {
    private var recorder: AudioRecord? = null
    private var worker: Thread? = null
    private var startedAt = 0L
    @Volatile private var recording = false

    fun isRecording(): Boolean = recording

    @Synchronized
    fun start(): Boolean {
        if (recording) return false
        val minBuffer = AudioRecord.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        )
        if (minBuffer <= 0) return false

        val bufferSize = maxOf(minBuffer * 2, sampleRate / 2)
        val audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            bufferSize
        )
        if (audioRecord.state != AudioRecord.STATE_INITIALIZED) {
            audioRecord.release()
            return false
        }

        outputDir.mkdirs()
        recorder = audioRecord
        recording = true
        startedAt = System.currentTimeMillis()

        worker = Thread {
            val pcm = ByteArrayOutputStream()
            val buffer = ByteArray(bufferSize)
            try {
                audioRecord.startRecording()
                while (recording && System.currentTimeMillis() - startedAt < maxDurationMs) {
                    val read = audioRecord.read(buffer, 0, buffer.size)
                    if (read > 0) pcm.write(buffer, 0, read)
                }
            } finally {
                recording = false
                runCatching { audioRecord.stop() }
                audioRecord.release()
                recorder = null
                val wav = File(outputDir, "mie-" + System.currentTimeMillis() + ".wav")
                writeWav(wav, pcm.toByteArray())
                lastFile = wav
            }
        }.apply {
            name = "mie-audio-recorder"
            start()
        }
        return true
    }

    @Synchronized
    fun stop() {
        recording = false
        worker?.join(1500L)
        worker = null
    }

    @Volatile var lastFile: File? = null
        private set

    fun durationMs(file: File): Long {
        val pcmBytes = (file.length() - 44L).coerceAtLeast(0L)
        return (pcmBytes * 1000L) / (sampleRate * 2L)
    }

    private fun writeWav(file: File, pcm: ByteArray) {
        FileOutputStream(file).use { out ->
            val byteRate = sampleRate * 2
            val dataLength = pcm.size
            val chunkSize = 36 + dataLength
            out.write("RIFF".toByteArray(Charsets.US_ASCII))
            writeIntLE(out, chunkSize)
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
