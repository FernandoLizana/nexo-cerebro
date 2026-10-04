package org.nexo.node

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme

/** Limited phone node. Same house, same four gestures, nothing else. */
class NodoActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        PresenceClient.applyLabIntentExtras(this, intent)
        val autoGreet = intent?.getBooleanExtra(PresenceClient.EXTRA_AUTO_GREET, false) == true
        setContent {
            MaterialTheme {
                PresenceHome(
                    title = "NEXO Nodo",
                    source = "android-nodo",
                    blurb = "Otro celular en la misma casa. No lee el teléfono. Habla con los nodos.",
                    autoGreetOnStart = autoGreet,
                    onStop = {
                        startService(
                            Intent(this, NodeForegroundService::class.java)
                                .setAction(NodeForegroundService.ACTION_STOP)
                        )
                    },
                )
            }
        }
    }
}
