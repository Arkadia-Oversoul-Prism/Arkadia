package com.sonata.app.service

import android.app.Activity
import android.app.Dialog
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import android.widget.FrameLayout
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.sonata.app.ui.theme.Accent
import kotlinx.coroutines.delay

class ProcessTextActivity : Activity() {
    
    private var selectedText: String = ""
    private var isPlaying = false
    private var dialog: Dialog? = null
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        handleIntent(intent)
        
        if (selectedText.isNotEmpty()) {
            showOverlay()
        } else {
            finish()
        }
    }
    
    private fun showOverlay() {
        val context = this
        
        val contentView = ComposeView(context).apply {
            setContent {
                ProcessTextOverlay(
                    text = selectedText,
                    onDismiss = { 
                        stopTtsService()
                        finish() 
                    },
                    onPlay = { 
                        startTtsService()
                        isPlaying = true
                    },
                    onPause = { 
                        pauseTtsService()
                        isPlaying = false
                    },
                    onStop = { 
                        stopTtsService()
                        finish()
                    }
                )
            }
        }
        
        dialog = Dialog(context, android.R.style.Theme_Translucent_NoTitleBar).apply {
            setContentView(contentView)
            window?.setFlags(
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
            )
            show()
        }
    }
    
    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        intent?.let { handleIntent(it) }
    }
    
    private fun handleIntent(intent: Intent) {
        if (Intent.ACTION_PROCESS_TEXT == intent.action) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                val charSequence = intent.getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT)
                selectedText = charSequence?.toString() ?: ""
                
                if (selectedText.isNotEmpty()) {
                    startTtsService()
                }
            }
        }
    }
    
    private fun startTtsService() {
        val serviceIntent = Intent(this, TtsPlaybackService::class.java)
        startService(serviceIntent)
        
        bindService(serviceIntent, object : android.content.ServiceConnection {
            override fun onServiceConnected(name: android.content.ComponentName?, service: android.os.IBinder?) {
                val binder = service as? TtsPlaybackService.TtsBinder
                val ttsService = binder?.getService()
                ttsService?.speak(selectedText)
            }
            
            override fun onServiceDisconnected(name: android.content.ComponentName?) {}
        }, android.content.Context.BIND_AUTO_CREATE)
    }
    
    private fun pauseTtsService() {
        val serviceIntent = Intent(this, TtsPlaybackService::class.java)
        serviceIntent.action = TtsPlaybackService.ACTION_PAUSE
        startService(serviceIntent)
    }
    
    private fun stopTtsService() {
        val serviceIntent = Intent(this, TtsPlaybackService::class.java)
        serviceIntent.action = TtsPlaybackService.ACTION_STOP
        startService(serviceIntent)
    }
    
    override fun onDestroy() {
        dialog?.dismiss()
        super.onDestroy()
    }
}

@Composable
fun ProcessTextOverlay(
    text: String,
    onDismiss: () -> Unit,
    onPlay: () -> Unit,
    onPause: () -> Unit,
    onStop: () -> Unit
) {
    var isPlaying by remember { mutableStateOf(true) }
    var showOverlay by remember { mutableStateOf(true) }
    
    LaunchedEffect(Unit) {
        delay(3000)
        showOverlay = false
    }
    
    if (showOverlay) {
        Dialog(
            onDismissRequest = {
                onStop()
                onDismiss()
            },
            properties = DialogProperties(
                dismissOnBackPress = true,
                dismissOnClickOutside = true,
                usePlatformDefaultWidth = false
            )
        ) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                shape = RoundedCornerShape(16.dp),
                color = Color(0xE6121214),
                tonalElevation = 8.dp
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(
                            onClick = {
                                if (isPlaying) {
                                    onPause()
                                } else {
                                    onPlay()
                                }
                                isPlaying = !isPlaying
                            },
                            modifier = Modifier
                                .size(48.dp)
                                .clip(CircleShape)
                                .background(Accent)
                        ) {
                            Icon(
                                imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                                contentDescription = if (isPlaying) "Pause" else "Play",
                                tint = Color.White,
                                modifier = Modifier.size(24.dp)
                            )
                        }
                        
                        Spacer(modifier = Modifier.width(16.dp))
                        
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "Speaking with Sonata",
                                style = MaterialTheme.typography.labelMedium,
                                color = Color.White.copy(alpha = 0.6f)
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = text.take(100) + if (text.length > 100) "..." else "",
                                style = MaterialTheme.typography.bodyMedium,
                                color = Color.White,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                        
                        IconButton(onClick = {
                            onStop()
                            onDismiss()
                        }) {
                            Icon(
                                imageVector = Icons.Default.Stop,
                                contentDescription = "Stop",
                                tint = Color.White.copy(alpha = 0.7f)
                            )
                        }
                        
                        IconButton(onClick = {
                            onStop()
                            onDismiss()
                        }) {
                            Icon(
                                imageVector = Icons.Default.Close,
                                contentDescription = "Close",
                                tint = Color.White.copy(alpha = 0.5f)
                            )
                        }
                    }
                }
            }
        }
    }
}