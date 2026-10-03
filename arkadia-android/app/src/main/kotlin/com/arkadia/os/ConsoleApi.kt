package com.arkadia.os

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

data class ConsoleSnapshot(
    val workspace: JSONObject?,
    val pulse: JSONObject?,
    val workload: JSONObject?,
    val synthesis: JSONObject?,
    val proposals: List<JSONObject>,
    val events: List<JSONObject>
)

class ConsoleApi(private val prefs: Prefs) {
    private val client = OkHttpClient()
    private val jsonType = "application/json".toMediaType()

    private fun request(path: String, method: String = "GET", body: String? = null): JSONObject {
        val builder = Request.Builder().url(prefs.apiUrl.trimEnd('/') + path).header("Accept", "application/json")
        prefs.apiToken.trim().takeIf { it.isNotEmpty() }?.let { builder.header("Authorization", "Bearer $it") }
        if (body != null) builder.method(method, body.toRequestBody(jsonType))
        val response = client.newCall(builder.build()).execute()
        val text = response.body?.string().orEmpty()
        if (!response.isSuccessful) error("HTTP ${response.code}: ${text.take(220)}")
        return if (text.isBlank()) JSONObject() else JSONObject(text)
    }

    suspend fun snapshot(): ConsoleSnapshot = withContext(Dispatchers.IO) {
        fun get(path: String): JSONObject? = runCatching { request(path) }.getOrNull()
        fun array(path: String, key: String): List<JSONObject> {
            val root = runCatching { request(path) }.getOrNull() ?: return emptyList()
            val arr = root.optJSONArray(key) ?: return emptyList()
            return (0 until arr.length()).mapNotNull { arr.optJSONObject(it) }
        }
        ConsoleSnapshot(
            workspace = get("/solspire/workspace")?.optJSONObject("workspace"),
            pulse = get("/solspire/pulses/today")?.optJSONObject("pulse"),
            workload = get("/solspire/workloads")?.optJSONObject("workload"),
            synthesis = get("/solspire/syntheses/current")?.optJSONObject("synthesis"),
            proposals = array("/solspire/proposals?limit=20", "proposals"),
            events = array("/solspire/workevents?limit=8", "work_events")
        )
    }

    suspend fun decide(proposalId: String, decision: String): JSONObject = withContext(Dispatchers.IO) {
        request("/solspire/proposals/$proposalId/decision", "POST", JSONObject().put("decision", decision).toString())
    }

    suspend fun askArkana(message: String): String = withContext(Dispatchers.IO) {
        val root = request("/api/commune/resonance", "POST",
            JSONObject().put("message", message).put("history", emptyList<String>()).put("session_id", prefs.sessionId).toString())
        root.optString("reply").ifBlank { root.optString("response", "No response returned.") }
    }

    suspend fun emitCapture(title: String, text: String, artifactRef: String? = null): JSONObject =
        withContext(Dispatchers.IO) {
            val refs = org.json.JSONArray()
            if (artifactRef != null) refs.put(artifactRef)
            val body = JSONObject()
                .put("event_type", "CAPTURED")
                .put("occurred_at", System.currentTimeMillis() / 1000.0)
                .put("status", "RECORDED")
                .put("schema_version", "1")
                .put("artifact_refs", refs)
                .put("state_after_ref", title)
                .put("work_ref", text.take(500))
            request("/solspire/workevents", "POST", body.toString())
        }
}
