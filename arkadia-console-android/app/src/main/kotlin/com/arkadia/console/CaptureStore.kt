package com.arkadia.console

import android.content.Context
import android.net.Uri
import java.io.File
import java.io.FileInputStream
import java.security.MessageDigest
import java.time.Instant
import java.util.UUID
import org.json.JSONArray
import org.json.JSONObject

data class CaptureRecord(val id:String,val kind:String,val path:String,val mimeType:String,val sizeBytes:Long,val sha256:String,val capturedAt:String){
    fun toJson()=JSONObject().apply{put("id",id);put("kind",kind);put("path",path);put("mime_type",mimeType);put("size_bytes",sizeBytes);put("sha256",sha256);put("captured_at",capturedAt)}
}

class CaptureStore(private val context:Context){
    private val prefs=context.getSharedPreferences("arkadia_captures",Context.MODE_PRIVATE)
    private val dir=File(context.filesDir,"captures").apply{mkdirs()}
    fun newFile(extension:String):Pair<String,File>{val id="CAP-"+UUID.randomUUID().toString().replace("-","").take(16);return id to File(dir,"$id.$extension")}
    fun record(id:String,kind:String,file:File,mimeType:String):CaptureRecord{
        val record=CaptureRecord(id,kind,file.absolutePath,mimeType,file.length(),sha256(file),Instant.now().toString())
        val all=JSONArray(prefs.getString("records","[]") ?: "[]");all.put(record.toJson());prefs.edit().putString("records",all.toString()).apply();return record
    }
    fun copyUri(id:String,uri:Uri,mimeType:String,extension:String):CaptureRecord{
        val target=File(dir,"$id.$extension")
        context.contentResolver.openInputStream(uri).use{input->requireNotNull(input){"Unable to open selected file"};target.outputStream().use{output->input.copyTo(output)}}
        return record(id,"file",target,mimeType)
    }
    fun records():List<CaptureRecord>{
        val all=JSONArray(prefs.getString("records","[]") ?: "[]")
        return (0 until all.length()).mapNotNull{idx->val o=all.optJSONObject(idx) ?: return@mapNotNull null;CaptureRecord(o.optString("id"),o.optString("kind"),o.optString("path"),o.optString("mime_type"),o.optLong("size_bytes"),o.optString("sha256"),o.optString("captured_at"))}.reversed()
    }
    private fun sha256(file:File):String{val digest=MessageDigest.getInstance("SHA-256");FileInputStream(file).use{input->val buffer=ByteArray(8192);while(true){val n=input.read(buffer);if(n<0)break;digest.update(buffer,0,n)}};return digest.digest().joinToString(""){"%02x".format(it)}}
}
