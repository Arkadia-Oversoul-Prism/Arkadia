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
import java.util.UUID

data class ChatMessage(val role: String, val text: String)

class OracleFragment : Fragment() {

    private lateinit var repo: ArkadiaRepository
    private lateinit var messagesContainer: LinearLayout
    private lateinit var scrollView: ScrollView
    private lateinit var etInput: EditText
    private lateinit var btnSend: Button
    private lateinit var tvStatus: TextView

    private val threadId = "android-${UUID.randomUUID()}"
    private val history = mutableListOf<ChatMessage>()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        return inflater.inflate(R.layout.fragment_oracle, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        repo = (requireActivity() as KnowledgeActivity).repository

        messagesContainer = view.findViewById(R.id.oracleMessagesContainer)
        scrollView        = view.findViewById(R.id.oracleScrollView)
        etInput           = view.findViewById(R.id.etOracleInput)
        btnSend           = view.findViewById(R.id.btnOracleSend)
        tvStatus          = view.findViewById(R.id.tvOracleStatus)

        addSystemMessage("Knowledge OS · Oracle · Ready\nAsk anything from your Knowledge Vault.")

        btnSend.setOnClickListener { sendMessage() }
        etInput.setOnEditorActionListener { _, _, _ -> sendMessage(); true }
    }

    private fun sendMessage() {
        val text = etInput.text?.toString()?.trim() ?: return
        if (text.isEmpty()) return

        etInput.text?.clear()
        btnSend.isEnabled = false
        tvStatus.text = "Oracle thinking…"

        addBubble("You", text, isUser = true)
        history.add(ChatMessage("user", text))

        lifecycleScope.launch {
            try {
                val resp = repo.send(text, threadId)
                if (!isAdded) return@launch

                history.add(ChatMessage("oracle", resp.content))
                addBubble("Oracle · ${resp.provider}", resp.content, isUser = false)

                val noteNote = if (resp.noteId != null) " · saved to vault" else ""
                tvStatus.text = "Via ${resp.provider}$noteNote"
            } catch (e: Exception) {
                if (isAdded) {
                    addBubble("System", "Error: ${e.message?.take(120)}", isUser = false)
                    tvStatus.text = "Connection error"
                }
            } finally {
                if (isAdded) btnSend.isEnabled = true
            }
        }
    }

    private fun addSystemMessage(text: String) {
        val tv = TextView(requireContext()).apply {
            this.text = text
            textSize = 10f
            setTextColor(Color.parseColor("#55606A"))
            gravity = android.view.Gravity.CENTER
            letterSpacing = 0.05f
            val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            lp.setMargins(0, 0, 0, dp(16))
            layoutParams = lp
            setPadding(dp(12), dp(10), dp(12), dp(10))
        }
        messagesContainer.addView(tv)
    }

    private fun addBubble(sender: String, text: String, isUser: Boolean) {
        val wrapper = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            gravity = if (isUser) android.view.Gravity.END else android.view.Gravity.START
            val lp = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            lp.setMargins(0, 0, 0, dp(12))
            layoutParams = lp
        }

        val tvSender = TextView(requireContext()).apply {
            this.text = sender.uppercase()
            textSize = 8f
            setTextColor(if (isUser) Color.parseColor("#C9A84C") else Color.parseColor("#00D4AA"))
            letterSpacing = 0.18f
            setPadding(if (isUser) 0 else dp(4), 0, if (isUser) dp(4) else 0, dp(3))
            gravity = if (isUser) android.view.Gravity.END else android.view.Gravity.START
        }
        wrapper.addView(tvSender)

        val bubble = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(if (isUser) Color.parseColor("#1A1A2E") else Color.parseColor("#12121E"))
            setPadding(dp(14), dp(12), dp(14), dp(12))
            val bubbleLp = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply {
                gravity = if (isUser) android.view.Gravity.END else android.view.Gravity.START
                marginStart = if (isUser) dp(48) else 0
                marginEnd = if (isUser) 0 else dp(48)
            }
            layoutParams = bubbleLp
        }

        val tvText = TextView(requireContext()).apply {
            this.text = text
            textSize = 13f
            setTextColor(Color.parseColor("#D4C9B8"))
            setLineSpacing(0f, 1.5f)
        }
        bubble.addView(tvText)
        wrapper.addView(bubble)

        messagesContainer.addView(wrapper)
        scrollView.post { scrollView.fullScroll(View.FOCUS_DOWN) }
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
