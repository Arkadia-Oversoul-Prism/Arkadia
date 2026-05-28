package com.arkadia.sonata

import android.os.Bundle
import android.widget.SeekBar
import android.widget.Switch
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.arkadia.sonata.databinding.ActivitySettingsBinding

class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding
    private lateinit var prefs: Prefs

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs   = Prefs(this)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        title = getString(R.string.settings)

        setupSpeedSeek()
        setupPitchSeek()
        setupSwitches()
        setupEdgeTtsUrl()
        setupStorageManagement()
    }

    override fun onSupportNavigateUp(): Boolean { finish(); return true }

    private val speeds = listOf(0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 1.75f, 2.0f)

    private fun setupSpeedSeek() {
        binding.seekSpeed.max      = speeds.size - 1
        binding.seekSpeed.progress = speeds.indexOfFirst { it == prefs.speed }.coerceAtLeast(2)
        updateLabel(binding.tvSpeedValue, prefs.speed, "×")
        binding.seekSpeed.setOnSeekBarChangeListener(seek { prefs.speed = it; updateLabel(binding.tvSpeedValue, it, "×") })
    }

    private fun setupPitchSeek() {
        val pitches = listOf(0.5f, 0.75f, 1.0f, 1.25f, 1.5f)
        binding.seekPitch.max      = pitches.size - 1
        binding.seekPitch.progress = pitches.indexOfFirst { it == prefs.pitch }.coerceAtLeast(2)
        updateLabel(binding.tvPitchValue, prefs.pitch, "×")
        binding.seekPitch.setOnSeekBarChangeListener(seek { prefs.pitch = it; updateLabel(binding.tvPitchValue, it, "×") })
    }

    private fun setupSwitches() {
        binding.switchAutoRead.isChecked    = prefs.autoRead
        binding.switchPreferEdge.isChecked  = prefs.preferEdgeTts

        binding.switchAutoRead.setOnCheckedChangeListener { _, checked -> prefs.autoRead     = checked }
        binding.switchPreferEdge.setOnCheckedChangeListener { _, checked -> prefs.preferEdgeTts = checked }
    }

    private fun setupEdgeTtsUrl() {
        binding.etEdgeTtsUrl.setText(prefs.edgeTtsUrl)
        binding.btnSaveUrl.setOnClickListener {
            prefs.edgeTtsUrl = binding.etEdgeTtsUrl.text?.toString()?.trim() ?: ""
            android.widget.Toast.makeText(this, "Saved", android.widget.Toast.LENGTH_SHORT).show()
        }
    }

    private fun setupStorageManagement() {
        val cacheDir  = cacheDir
        val cacheSize = (cacheDir.walkTopDown().sumOf { if (it.isFile) it.length() else 0L }) / 1024
        binding.tvCacheSize.text = "$cacheSize KB cached audio"
        binding.btnClearCache.setOnClickListener {
            cacheDir.walkTopDown().filter { it.name.startsWith("sonata_") && it.name.endsWith(".mp3") }
                .forEach { it.delete() }
            binding.tvCacheSize.text = "0 KB cached audio"
            android.widget.Toast.makeText(this, "Cache cleared", android.widget.Toast.LENGTH_SHORT).show()
        }
    }

    private fun updateLabel(tv: TextView, v: Float, suffix: String) { tv.text = "$v$suffix" }

    private fun seek(onValue: (Float) -> Unit) = object : SeekBar.OnSeekBarChangeListener {
        override fun onProgressChanged(sb: SeekBar, p: Int, fromUser: Boolean) {
            onValue(speeds.getOrElse(p) { 1.0f })
        }
        override fun onStartTrackingTouch(sb: SeekBar) {}
        override fun onStopTrackingTouch(sb: SeekBar) {}
    }
}
