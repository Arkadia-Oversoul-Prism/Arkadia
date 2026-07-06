package com.arkadia.sonata

import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class SearchFragment : Fragment() {

    private lateinit var repo: ArkadiaRepository
    private lateinit var etQuery: EditText
    private lateinit var btnSearch: Button
    private lateinit var spinnerMode: Spinner
    private lateinit var tvStatus: TextView
    private lateinit var resultsContainer: LinearLayout
    private lateinit var scrollView: ScrollView

    private val modes = listOf("semantic", "fulltext", "tag", "graph", "project", "people", "reference")
    private val modeLabels = listOf("Semantic", "Full Text", "Tags", "Graph", "Project", "People", "Reference")

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        return inflater.inflate(R.layout.fragment_search, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        repo = (requireActivity() as KnowledgeActivity).repository

        etQuery       = view.findViewById(R.id.etSearchQuery)
        btnSearch     = view.findViewById(R.id.btnSearch)
        spinnerMode   = view.findViewById(R.id.spinnerSearchMode)
        tvStatus      = view.findViewById(R.id.tvSearchStatus)
        resultsContainer = view.findViewById(R.id.searchResultsContainer)
        scrollView    = view.findViewById(R.id.searchScrollView)

        val adapter = ArrayAdapter(requireContext(), android.R.layout.simple_spinner_item, modeLabels)
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        spinnerMode.adapter = adapter

        btnSearch.setOnClickListener { doSearch() }
        etQuery.setOnEditorActionListener { _, _, _ -> doSearch(); true }
    }

    private fun doSearch() {
        val query = etQuery.text?.toString()?.trim() ?: return
        if (query.isEmpty()) { tvStatus.text = "Enter a search query"; return }

        val modeIdx = spinnerMode.selectedItemPosition.coerceIn(0, modes.lastIndex)
        val mode = modes[modeIdx]

        tvStatus.text = "Searching…"
        btnSearch.isEnabled = false
        resultsContainer.removeAllViews()

        lifecycleScope.launch {
            try {
                val results = repo.search(query, mode)
                if (!isAdded) return@launch

                if (results.isEmpty()) {
                    tvStatus.text = "No results found"
                } else {
                    tvStatus.text = "${results.size} result${if (results.size != 1) "s" else ""}"
                    results.forEach { r -> resultsContainer.addView(buildResultCard(r)) }
                }
            } catch (e: Exception) {
                if (isAdded) tvStatus.text = "Error: ${e.message?.take(80)}"
            } finally {
                if (isAdded) btnSearch.isEnabled = true
            }
        }
    }

    private fun buildResultCard(r: SearchResult): View {
        val card = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(14), dp(14), dp(14), dp(14))
            setBackgroundColor(Color.parseColor("#12121E"))
            val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            lp.setMargins(0, 0, 0, dp(10))
            layoutParams = lp
        }

        val tvTitle = TextView(requireContext()).apply {
            text = r.title
            textSize = 14f
            setTextColor(Color.parseColor("#E8E8E8"))
            setPadding(0, 0, 0, dp(4))
        }
        card.addView(tvTitle)

        val tvMeta = TextView(requireContext()).apply {
            text = "${r.type.uppercase()}  ·  score ${String.format("%.2f", r.score)}"
            textSize = 9f
            setTextColor(Color.parseColor("#00D4AA"))
            letterSpacing = 0.12f
            setPadding(0, 0, 0, dp(6))
        }
        card.addView(tvMeta)

        if (r.content.isNotBlank()) {
            val tvContent = TextView(requireContext()).apply {
                text = r.content.take(220).let { if (r.content.length > 220) "$it…" else it }
                textSize = 12f
                setTextColor(Color.parseColor("#99A0B0"))
                setLineSpacing(0f, 1.5f)
                setPadding(0, 0, 0, dp(6))
            }
            card.addView(tvContent)
        }

        if (r.tags.isNotEmpty()) {
            val tvTags = TextView(requireContext()).apply {
                text = r.tags.take(5).joinToString("  ") { "#$it" }
                textSize = 10f
                setTextColor(Color.parseColor("#55606A"))
            }
            card.addView(tvTags)
        }

        return card
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
