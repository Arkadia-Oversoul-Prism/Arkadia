package com.arkadia.sonata

import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class TimelineFragment : Fragment() {

    private lateinit var repo: ArkadiaRepository
    private lateinit var eventsContainer: LinearLayout
    private lateinit var scrollView: ScrollView
    private lateinit var tvStatus: TextView
    private lateinit var btnRefresh: Button

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        return inflater.inflate(R.layout.fragment_timeline, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        repo = (requireActivity() as KnowledgeActivity).repository

        eventsContainer = view.findViewById(R.id.timelineEventsContainer)
        scrollView      = view.findViewById(R.id.timelineScrollView)
        tvStatus        = view.findViewById(R.id.tvTimelineStatus)
        btnRefresh      = view.findViewById(R.id.btnTimelineRefresh)

        btnRefresh.setOnClickListener { loadTimeline() }
        loadTimeline()
    }

    private fun loadTimeline() {
        tvStatus.text = "Loading timeline…"
        btnRefresh.isEnabled = false
        eventsContainer.removeAllViews()

        lifecycleScope.launch {
            try {
                val events = repo.timeline(40)
                if (!isAdded) return@launch

                if (events.isEmpty()) {
                    tvStatus.text = "No events yet · Send a message to begin"
                } else {
                    tvStatus.text = "${events.size} event${if (events.size != 1) "s" else ""} · immutable log"
                    events.forEach { e -> eventsContainer.addView(buildEventCard(e)) }
                }
            } catch (e: Exception) {
                if (isAdded) tvStatus.text = "Error: ${e.message?.take(80)}"
            } finally {
                if (isAdded) btnRefresh.isEnabled = true
            }
        }
    }

    private val eventColors = mapOf(
        "conversation"  to "#00D4AA",
        "decision"      to "#C9A84C",
        "knowledge"     to "#B08DE8",
        "system"        to "#6A9FD8",
        "note_created"  to "#4CAF50",
        "note_updated"  to "#3DE8D0",
    )

    private fun buildEventCard(e: TimelineEvent): View {
        val color = eventColors[e.eventType] ?: "#55606A"
        val colorInt = Color.parseColor(color)

        val row = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            lp.setMargins(0, 0, 0, dp(10))
            layoutParams = lp
        }

        val rail = View(requireContext()).apply {
            layoutParams = LinearLayout.LayoutParams(dp(3), LinearLayout.LayoutParams.MATCH_PARENT).apply {
                marginEnd = dp(12)
            }
            setBackgroundColor(colorInt)
        }
        row.addView(rail)

        val card = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            setBackgroundColor(Color.parseColor("#12121E"))
            setPadding(dp(12), dp(10), dp(12), dp(10))
        }

        val tvType = TextView(requireContext()).apply {
            text = "${e.eventType.replace('_', ' ').uppercase()}  ·  ${formatTimestamp(e.timestamp)}"
            textSize = 8.5f
            setTextColor(colorInt)
            letterSpacing = 0.15f
            setPadding(0, 0, 0, dp(3))
        }
        card.addView(tvType)

        val tvTitle = TextView(requireContext()).apply {
            text = e.title
            textSize = 13f
            setTextColor(Color.parseColor("#E8E8E8"))
            setPadding(0, 0, 0, if (e.summary.isNotBlank()) dp(4) else 0)
        }
        card.addView(tvTitle)

        if (e.summary.isNotBlank()) {
            val tvSum = TextView(requireContext()).apply {
                text = e.summary.take(180).let { if (e.summary.length > 180) "$it…" else it }
                textSize = 11.5f
                setTextColor(Color.parseColor("#99A0B0"))
                setLineSpacing(0f, 1.5f)
            }
            card.addView(tvSum)
        }

        row.addView(card)
        return row
    }

    private fun formatTimestamp(ts: String): String {
        if (ts.isBlank()) return "—"
        return try {
            ts.replace("T", " ").take(16)
        } catch (_: Exception) { ts.take(16) }
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
