package com.arkadia.sonata

import android.app.Service
import android.content.ComponentName
import android.content.Intent
import android.content.ServiceConnection
import android.graphics.PixelFormat
import android.os.IBinder
import android.view.Gravity
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.ImageButton
import android.widget.TextView
import com.arkadia.sonata.databinding.OverlayPlayerBinding

/**
 * Minimal draggable glass overlay for playback control.
 * Black glass aesthetic, always on top, draggable.
 *
 * Lifecycle: started by ProcessTextActivity → SpeechService bound internally.
 */
class FloatingOverlayService : Service() {

    private lateinit var wm: WindowManager
    private lateinit var binding: OverlayPlayerBinding
    private var overlayView: View? = null

    private var speechService: SpeechService? = null
    private val conn = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName, binder: IBinder) {
            speechService = (binder as SpeechService.LocalBinder).getService()
            speechService?.onStart    = { updatePlayPause() }
            speechService?.onPause    = { updatePlayPause() }
            speechService?.onResume   = { updatePlayPause() }
            speechService?.onComplete = { stopSelf() }
        }
        override fun onServiceDisconnected(name: ComponentName) { speechService = null }
    }

    // ── Window params ──────────────────────────────────────────────────────

    private val params = WindowManager.LayoutParams(
        WindowManager.LayoutParams.WRAP_CONTENT,
        WindowManager.LayoutParams.WRAP_CONTENT,
        WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
        WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
            WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
        PixelFormat.TRANSLUCENT
    ).apply {
        gravity = Gravity.TOP or Gravity.START
        x = 80
        y = 200
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────

    override fun onCreate() {
        super.onCreate()
        wm = getSystemService(WindowManager::class.java)

        binding = OverlayPlayerBinding.inflate(LayoutInflater.from(this))
        overlayView = binding.root

        setupDrag()
        setupButtons()

        wm.addView(overlayView, params)

        // Bind to SpeechService
        bindService(
            Intent(this, SpeechService::class.java),
            conn,
            BIND_AUTO_CREATE
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        intent?.getStringExtra(EXTRA_LABEL)?.let { binding.tvLabel.text = it }
        intent?.getStringExtra(EXTRA_PREVIEW)?.let { binding.tvPreview.text = it.take(60) + "…" }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        unbindService(conn)
        overlayView?.let { wm.removeView(it) }
        super.onDestroy()
    }

    // ── Drag ──────────────────────────────────────────────────────────────

    private var initX = 0; private var initY = 0
    private var initTouchX = 0f; private var initTouchY = 0f

    private fun setupDrag() {
        binding.root.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initX = params.x; initY = params.y
                    initTouchX = event.rawX; initTouchY = event.rawY
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    params.x = initX + (event.rawX - initTouchX).toInt()
                    params.y = initY + (event.rawY - initTouchY).toInt()
                    wm.updateViewLayout(overlayView, params)
                    true
                }
                else -> false
            }
        }
    }

    // ── Buttons ──────────────────────────────────────────────────────────

    private fun setupButtons() {
        binding.btnPlayPause.setOnClickListener {
            val svc = speechService ?: return@setOnClickListener
            if (svc.isPlaying) svc.pause() else svc.resume()
            updatePlayPause()
        }
        binding.btnStop.setOnClickListener {
            speechService?.stop()
            stopSelf()
        }
        binding.btnClose.setOnClickListener { stopSelf() }

        binding.btnSpeed.setOnClickListener {
            val prefs  = Prefs(this)
            val speeds = listOf(0.75f, 1.0f, 1.25f, 1.5f, 2.0f)
            val next   = speeds[(speeds.indexOf(prefs.speed).takeIf { it >= 0 } ?: 1) + 1 % speeds.size]
            prefs.speed = next
            binding.btnSpeed.text = "${next}×"
        }
    }

    private fun updatePlayPause() {
        val playing = speechService?.isPlaying == true
        binding.btnPlayPause.setImageResource(
            if (playing) android.R.drawable.ic_media_pause
            else         android.R.drawable.ic_media_play
        )
    }

    companion object {
        const val EXTRA_LABEL   = "label"
        const val EXTRA_PREVIEW = "preview"
    }
}
