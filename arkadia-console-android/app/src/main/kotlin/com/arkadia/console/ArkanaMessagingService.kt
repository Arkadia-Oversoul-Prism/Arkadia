package com.arkadia.console

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class ArkanaMessagingService:FirebaseMessagingService(){
    private val client by lazy { OkHttpClient() }

    override fun onNewToken(token:String){
        FirebaseIdentity.initialize(this)?.let{identity->
            CoroutineScope(Dispatchers.IO).launch{
                runCatching{
                    val idToken=identity.idToken(false) ?: return@launch
                    val json=JSONObject().put("token",token).put("platform","android").toString()
                    val request=Request.Builder()
                        .url(BuildConfig.ORACLE_BASE_URL.trimEnd('/')+"/api/google-workspace/push/device")
                        .header("Authorization","Bearer $idToken")
                        .post(json.toRequestBody("application/json".toMediaType()))
                        .build()
                    client.newCall(request).execute().close()
                }
            }
        }
    }

    override fun onMessageReceived(message:RemoteMessage){
        val data=message.data
        val title=message.notification?.title ?: "Arkana"
        val body=message.notification?.body ?: data["claim"] ?: data["event_type"] ?: "New Arkadia attention event"
        val manager=getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channelId="arkana_attention"
        if(android.os.Build.VERSION.SDK_INT>=android.os.Build.VERSION_CODES.O){
            manager.createNotificationChannel(
                NotificationChannel(channelId,"Arkana Attention",NotificationManager.IMPORTANCE_DEFAULT)
            )
        }
        val notification=NotificationCompat.Builder(this,channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setAutoCancel(true)
            .build()
        notification.let{manager.notify((data["event_id"] ?: System.currentTimeMillis().toString()).hashCode(),it)}
    }
}
