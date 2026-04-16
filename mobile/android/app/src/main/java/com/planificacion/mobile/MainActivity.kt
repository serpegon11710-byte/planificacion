package com.planificacion.mobile

import android.app.AlertDialog
import android.os.Bundle
import android.util.Log
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        try {
            setContentView(R.layout.activity_main)
            val web = findViewById<WebView>(R.id.webview)
            web.settings.javaScriptEnabled = true
            web.settings.domStorageEnabled = true
            web.webViewClient = WebViewClient()
            web.loadUrl("file:///android_asset/www/index.html")
        } catch (t: Throwable) {
            Log.e("MainActivity", "Startup error", t)
            try {
                AlertDialog.Builder(this)
                    .setTitle("Error en la app")
                    .setMessage(t.toString())
                    .setPositiveButton("OK", null)
                    .show()
            } catch (ignored: Throwable) {
                // fallback: nothing we can do
            }
            // rethrow so crash also appears in crash reports if needed
            throw t
        }
    }
}
