package com.sonata.app.service

import android.inputmethodservice.InputMethodService
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import android.content.Intent
import android.os.Build

class SonataIMEService : InputMethodService() {
    
    override fun onCreate() {
        super.onCreate()
    }
    
    override fun onStartInput(attribute: EditorInfo?, restarting: Boolean) {
        super.onStartInput(attribute, restarting)
    }
    
    override fun onFinishInput() {
        super.onFinishInput()
    }
    
    override fun onShowInputRequested(flags: Int, configChange: Boolean): Boolean {
        return false // Don't show standard keyboard UI
    }
    
    override fun onKeyDown(keyCode: Int, event: android.view.KeyEvent?): Boolean {
        return false
    }
    
    override fun onKeyUp(keyCode: Int, event: android.view.KeyEvent?): Boolean {
        return false
    }
}