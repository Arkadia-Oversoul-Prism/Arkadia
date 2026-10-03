package com.arkadia.console

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

data class FieldObject(val id:String,val type:String,val title:String,val summary:String,val state:String,val source:String)
data class Proposal(val id:String,val objective:String,val status:String)
data class FieldSnapshot(val objects:List<FieldObject>,val proposals:List<Proposal>,val eventCount:Int,val live:Boolean,val message:String?=null)

class ConsoleRepository(private val baseUrl:()->String, private val token:suspend ()->String?) {
    private val client=OkHttpClient.Builder().connectTimeout(15,TimeUnit.SECONDS).readTimeout(45,TimeUnit.SECONDS).build()
    private val json="application/json; charset=utf-8".toMediaType()
    private suspend fun request(path:String,method:String="GET",body:String?=null):JSONObject=withContext(Dispatchers.IO){
        val b=Request.Builder().url(baseUrl().trimEnd('/')+path)
        token()?.takeIf{it.isNotBlank()}?.let{b.header("Authorization","Bearer "+it)}
        if(body!=null)b.method(method,body.toRequestBody(json)) else b.method(method,null)
        client.newCall(b.build()).execute().use{resp->
            val raw=resp.body?.string().orEmpty()
            if(!resp.isSuccessful){
                val detail=runCatching{JSONObject(raw).optString("detail")}.getOrNull().orEmpty()
                throw IllegalStateException(if(detail.isNotBlank())detail else "Oracle "+resp.code)
            }
            if(raw.isBlank())JSONObject() else JSONObject(raw)
        }
    }
    private fun s(o:JSONObject?,vararg keys:String):String {
        if(o==null)return ""
        for(k in keys)if(o.has(k)&&!o.isNull(k)){val v=o.optString(k);if(v.isNotBlank())return v}
        return ""
    }
    suspend fun snapshot():FieldSnapshot=withContext(Dispatchers.IO){
        try{
            val w=runCatching{request("/solspire/workspace")}.getOrNull()?.optJSONObject("workspace")
            val p=runCatching{request("/solspire/pulses/today")}.getOrNull()?.optJSONObject("pulse")
            val work=runCatching{request("/solspire/workloads")}.getOrNull()?.optJSONObject("workload")
            val syn=runCatching{request("/solspire/syntheses/current")}.getOrNull()?.optJSONObject("synthesis")
            val pj=runCatching{request("/solspire/proposals?limit=20")}.getOrNull()
            val ej=runCatching{request("/solspire/workevents?limit=8")}.getOrNull()
            val objects=mutableListOf<FieldObject>()
            w?.let{objects+=FieldObject("workspace","WORLD",s(it,"display_name").ifBlank{"Solariun World"},s(it,"workspace_type","subject_binding").ifBlank{"Canonical workspace"},s(it,"lifecycle").ifBlank{"LIVE"},"/solspire/workspace")}
            p?.let{objects+=FieldObject("pulse","SIGNAL","Today's signal",s(it,"current_signal","signal","summary","state_summary").ifBlank{"No current signal recorded."},"LIVE","/solspire/pulses/today")}
            work?.let{objects+=FieldObject("workload","WORK",s(it,"title","display_name").ifBlank{"Current work"},s(it,"objective","phase").ifBlank{"Workload is present in the canonical field."},s(it,"status","phase").ifBlank{"UNKNOWN"},"/solspire/workloads")}
            syn?.let{objects+=FieldObject("synthesis","KNOWLEDGE","Current synthesis",s(it,"summary","synthesis_summary").ifBlank{"Synthesis exists but has no summary."},"DERIVED","/solspire/syntheses/current")}
            val proposals=mutableListOf<Proposal>()
            pj?.optJSONArray("proposals")?.let{arr->for(i in 0 until arr.length()){val x=arr.optJSONObject(i)?:continue;proposals+=Proposal(s(x,"proposal_id","id").ifBlank{"proposal-"+i},s(x,"objective","requested_decision").ifBlank{"Proposal"},s(x,"proposal_status","status").ifBlank{"UNKNOWN"})}}
            proposals.take(8).forEach{x->objects+=FieldObject(x.id,"PROPOSAL",x.objective,"Human decision surface. Decision is not execution.",x.status,"/solspire/proposals/"+x.id+"/decision")}
            val events=ej?.let{it.optJSONArray("work_events")?.length()?:it.optJSONArray("events")?.length()?:0}?:0
            FieldSnapshot(objects,proposals,events,true)
        }catch(e:Exception){FieldSnapshot(emptyList(),emptyList(),0,false,e.message?:"Oracle unreachable")}
    }
    suspend fun askArkana(prompt:String):String=withContext(Dispatchers.IO){
        val body=JSONObject().apply{
            put("messages",JSONArray().put(JSONObject().put("role","user").put("content",prompt)))
            put("provider","gemini");put("persona","architect");put("ingest_response",true)
        }.toString()
        request("/api/knowledge/providers/send","POST",body).optString("content").ifBlank{"Arkana returned no content."}
    }
    suspend fun authorize(proposalId:String):String=withContext(Dispatchers.IO){
        val r=request("/solspire/authority/proposals/"+java.net.URLEncoder.encode(proposalId,"UTF-8")+"/authorize","POST","{}")
        val auth=r.optJSONObject("authorization")
        auth?.optString("id") ?: error("Authorization was not returned")
    }

    suspend fun createExecutionAttempt(authorizationId:String, toolChannel:String, payload:org.json.JSONObject):String=withContext(Dispatchers.IO){
        val r=request("/solspire/authority/authorizations/"+java.net.URLEncoder.encode(authorizationId,"UTF-8")+"/execute","POST",org.json.JSONObject().put("tool_channel",toolChannel).put("request_payload",payload).toString())
        r.optJSONObject("execution_attempt")?.optString("id") ?: error("Execution attempt was not returned")
    }

    suspend fun recordEvidence(executionId:String, evidenceType:String, content:String):String=withContext(Dispatchers.IO){
        val r=request("/solspire/authority/executions/"+java.net.URLEncoder.encode(executionId,"UTF-8")+"/evidence","POST",org.json.JSONObject().put("evidence_type",evidenceType).put("content_or_ref",content).toString())
        r.optJSONObject("evidence")?.optString("id") ?: error("Evidence was not returned")
    }

    suspend fun verify(claim:String,evidenceId:String,verdict:String):String=withContext(Dispatchers.IO){
        val r=request("/solspire/authority/verification","POST",org.json.JSONObject().put("claim",claim).put("evidence_refs",org.json.JSONArray().put(evidenceId)).put("verdict",verdict).toString())
        r.optJSONObject("verification")?.optString("id") ?: error("Verification was not returned")
    }

    suspend fun decide(id:String,decision:String):String{
        request("/solspire/proposals/"+java.net.URLEncoder.encode(id,"UTF-8")+"/decision","POST",JSONObject().put("decision",decision).toString())
        return "Decision recorded. Weaver execution remains separately governed."
    }
    suspend fun recordEvent(summary:String):String{
        val body=JSONObject().put("event_type","CONSOLE_CAPTURE").put("status","RECORDED").put("schema_version","1").put("artifact_refs",JSONArray()).put("summary",summary).toString()
        request("/solspire/workevents","POST",body);return "Reality captured as a WorkEvent."
    }
}
