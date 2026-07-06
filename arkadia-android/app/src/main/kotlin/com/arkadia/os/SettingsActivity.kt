package com.arkadia.os

import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.MenuItem
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.arkadia.os.databinding.ActivitySettingsBinding

class SettingsActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySettingsBinding
    private lateinit var prefs: Prefs

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs   = Prefs(this)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            title = "Arkadia Settings"
        }

        binding.etArkadiaUrl.setText(prefs.arkadiaUrl)

        binding.btnSaveUrl.setOnClickListener {
            val url = binding.etArkadiaUrl.text?.toString()?.trim() ?: ""
            prefs.arkadiaUrl = url
            binding.tvSaveStatus.text = "Saved ✓"
        }

        binding.btnEmulator.setOnClickListener {
            binding.etArkadiaUrl.setText(Prefs.DEFAULT_URL)
        }

        binding.etArkadiaUrl.addTextChangedListener(object : TextWatcher {
            override fun afterTextChanged(s: Editable?) { binding.tvSaveStatus.text = "" }
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
        })
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        if (item.itemId == android.R.id.home) { finish(); return true }
        return super.onOptionsItemSelected(item)
    }
}
