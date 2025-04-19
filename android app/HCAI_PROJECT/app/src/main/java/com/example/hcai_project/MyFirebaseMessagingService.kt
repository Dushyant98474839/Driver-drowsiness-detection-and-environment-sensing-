package com.example.hcai_project

import android.content.Intent
import android.util.Log
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class MyFirebaseMessagingService : FirebaseMessagingService() {

    companion object {
        const val ACTION_ALERT = "com.example.hcai_project.ALERT"
        const val EXTRA_TITLE = "title"
        const val EXTRA_MESSAGE = "message"
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d("FCM", "FCM Token: $token")
        // TODO: Send this token to your server
    }

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        super.onMessageReceived(remoteMessage)
        Log.d("FCM", "Message received: ${remoteMessage.notification?.body}")

        // Handle notification messages (foreground)
        remoteMessage.notification?.let {
            val title = it.title ?: "Alert"
            val body = it.body ?: "No message"
            sendAlertBroadcast(title, body)
        }

        // Handle data messages (optional, for background)
        remoteMessage.data.let { data ->
            if (data.isNotEmpty()) {
                val title = data["title"] ?: "Alert"
                val message = data["message"] ?: "No message"
                sendAlertBroadcast(title, message)
            }
        }
    }

    private fun sendAlertBroadcast(title: String, message: String) {
        val intent = Intent(ACTION_ALERT).apply {
            putExtra(EXTRA_TITLE, title)
            putExtra(EXTRA_MESSAGE, message)
        }
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent)
    }
}