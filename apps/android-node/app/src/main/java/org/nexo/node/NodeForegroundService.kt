package org.nexo.node

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat

class NodeForegroundService : Service() {
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            NodeSession.markStopped()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return START_NOT_STICKY
        }
        startForeground(NOTICE_ID, notification())
        NodeSession.markRunning()
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        NodeSession.markStopped()
        super.onDestroy()
    }

    private fun notification(): Notification {
        val channelId = "nexo-node"
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(
            NotificationChannel(channelId, "NEXO Node", NotificationManager.IMPORTANCE_LOW)
        )
        val stop = PendingIntent.getService(
            this,
            1,
            Intent(this, NodeForegroundService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("NEXO Node activo")
            .setContentText("Experimento Tier 0. No es un control remoto.")
            .addAction(android.R.drawable.ic_delete, "STOP NEXO NODE", stop)
            .setOngoing(true)
            .build()
    }

    companion object {
        const val ACTION_STOP = "org.nexo.node.STOP"
        private const val NOTICE_ID = 70
    }
}

object NodeSession {
    @Volatile var running: Boolean = false
        private set

    fun markRunning() { running = true }
    fun markStopped() { running = false }
}
