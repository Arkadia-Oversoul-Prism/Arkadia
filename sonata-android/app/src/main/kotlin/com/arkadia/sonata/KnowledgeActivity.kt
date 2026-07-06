package com.arkadia.sonata

import android.os.Bundle
import android.view.MenuItem
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView

class KnowledgeActivity : AppCompatActivity() {

    private lateinit var prefs: Prefs
    lateinit var repository: ArkadiaRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_knowledge)

        prefs = Prefs(this)
        val base = prefs.edgeTtsUrl.ifBlank { "http://10.0.2.2:8000" }
        repository = ArkadiaRepository(base)

        val nav = findViewById<BottomNavigationView>(R.id.bottomNavKnowledge)
        nav.setOnItemSelectedListener { item -> switchTab(item); true }

        if (savedInstanceState == null) {
            switchTab(nav.menu.findItem(R.id.nav_search))
        }
    }

    private fun switchTab(item: MenuItem) {
        val fragment: Fragment = when (item.itemId) {
            R.id.nav_search   -> SearchFragment()
            R.id.nav_oracle   -> OracleFragment()
            R.id.nav_timeline -> TimelineFragment()
            else              -> SearchFragment()
        }
        supportFragmentManager.beginTransaction()
            .replace(R.id.knowledgeFragmentContainer, fragment)
            .commit()
    }
}
