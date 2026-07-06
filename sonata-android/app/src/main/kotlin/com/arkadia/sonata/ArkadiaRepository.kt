package com.arkadia.sonata

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

data class SearchResult(
    val id: String,
    val title: String,
    val content: String,
    val tags: List<String>,
    val score: Double,
    val type: String,
)

data class TimelineEvent(
    val id: String,
    val eventType: String,
    val title: String,
    val summary: String,
    val timestamp: String,
)

data class OracleResponse(
    val content: String,
    val provider: String,
    val noteId: String?,
)

data class KnowledgeStatus(
    val totalNotes: Int,
    val totalChunks: Int,
    val graphEdges: Int,
    val timelineEvents: Int,
    val providerCount: Int,
)

/**
 * Single HTTP client for all Knowledge OS API calls.
 * Base URL is read from Prefs (same edgeTtsUrl the user already configured).
 */
class ArkadiaRepository(private val baseUrl: String) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val JSON = "application/json; charset=utf-8".toMediaType()

    private fun cleanBase(): String = baseUrl.trimEnd('/')

    // ── SEARCH ──────────────────────────────────────────────────────────────
    // Uses GET /api/knowledge/search/semantic — returns a flat JSONArray of
    // {note_uuid, title, note_type, content, score, chunk_id, note_id}

    suspend fun search(query: String, mode: String = "semantic", limit: Int = 12): List<SearchResult> =
        withContext(Dispatchers.IO) {
            val encodedQ = java.net.URLEncoder.encode(query, "UTF-8")
            val url = when (mode) {
                "fulltext" -> "${cleanBase()}/api/knowledge/search/fulltext?q=$encodedQ&limit=$limit"
                else       -> "${cleanBase()}/api/knowledge/search/semantic?q=$encodedQ&top_k=$limit"
            }

            val req = Request.Builder().url(url).get().build()
            val resp = client.newCall(req).execute()
            if (!resp.isSuccessful) return@withContext emptyList()

            val raw = resp.body?.string() ?: return@withContext emptyList()
            val results = org.json.JSONArray(raw)

            (0 until results.length()).mapNotNull { i ->
                runCatching {
                    val r = results.getJSONObject(i)
                    SearchResult(
                        id      = r.optString("note_uuid", r.optString("id", "")),
                        title   = r.optString("title", "Untitled"),
                        content = r.optString("content", ""),
                        tags    = emptyList(),
                        score   = r.optDouble("score", 0.0),
                        type    = r.optString("note_type", r.optString("type", "note")),
                    )
                }.getOrNull()
            }
        }

    // ── ORACLE SEND ──────────────────────────────────────────────────────────
    // SendRequest.messages = list[{role, content}], provider, persona, ingest_response

    suspend fun send(
        content: String,
        threadId: String = "android-session",
        provider: String = "gemini",
        persona: String = "architect",
    ): OracleResponse = withContext(Dispatchers.IO) {
        val userMsg = JSONObject().apply {
            put("role", "user")
            put("content", content)
        }
        val body = JSONObject().apply {
            put("messages", JSONArray().apply { put(userMsg) })
            put("provider", provider)
            put("persona", persona)
            put("ingest_response", true)
        }.toString().toRequestBody(JSON)

        val req = Request.Builder()
            .url("${cleanBase()}/api/knowledge/providers/send")
            .post(body)
            .build()

        val resp = client.newCall(req).execute()
        val raw = resp.body?.string() ?: "{}"
        val json = JSONObject(raw)

        OracleResponse(
            content  = json.optString("content", if (!resp.isSuccessful) "Error: ${resp.code}" else "No response"),
            provider = json.optString("provider", provider),
            noteId   = json.optString("note_id", null),
        )
    }

    // ── TIMELINE ─────────────────────────────────────────────────────────────
    // GET /api/knowledge/timeline returns a flat JSONArray of timeline rows.
    // Rows: {id, event_type, created_at, title, summary, payload, ...}

    suspend fun timeline(limit: Int = 40): List<TimelineEvent> = withContext(Dispatchers.IO) {
        val req = Request.Builder()
            .url("${cleanBase()}/api/knowledge/timeline?limit=$limit")
            .get()
            .build()

        val resp = client.newCall(req).execute()
        if (!resp.isSuccessful) return@withContext emptyList()

        val raw = resp.body?.string() ?: return@withContext emptyList()
        val arr = org.json.JSONArray(raw)

        (0 until arr.length()).mapNotNull { i ->
            runCatching {
                val e = arr.getJSONObject(i)
                TimelineEvent(
                    id        = e.optString("id", ""),
                    eventType = e.optString("event_type", "event"),
                    title     = e.optString("title", "Event"),
                    summary   = e.optString("summary", ""),
                    timestamp = e.optString("created_at", ""),
                )
            }.getOrNull()
        }.reversed()
    }

    // ── STATUS ───────────────────────────────────────────────────────────────

    suspend fun status(): KnowledgeStatus = withContext(Dispatchers.IO) {
        val req = Request.Builder()
            .url("${cleanBase()}/api/knowledge/status")
            .get()
            .build()

        val resp = client.newCall(req).execute()
        val json = JSONObject(resp.body?.string() ?: "{}")

        val db = json.optJSONObject("database") ?: JSONObject()
        val providers = json.optJSONObject("providers") ?: JSONObject()

        KnowledgeStatus(
            totalNotes    = db.optInt("notes", 0),
            totalChunks   = db.optInt("chunks", 0),
            graphEdges    = json.optJSONObject("graph")?.optInt("edges", 0) ?: 0,
            timelineEvents = db.optInt("timeline_events", 0),
            providerCount = providers.optInt("configured", 0),
        )
    }
}
