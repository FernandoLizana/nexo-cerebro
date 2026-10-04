package org.nexo.node

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (intent?.action == NodeForegroundService.ACTION_STOP) {
            stopService(Intent(this, NodeForegroundService::class.java))
        }
        setContent {
            MaterialTheme {
                val context = LocalContext.current
                var screen by remember { mutableStateOf("welcome") }
                var log by remember { mutableStateOf("sin experimento") }
                Column(
                    modifier = Modifier.fillMaxSize().padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("NEXO Node", style = MaterialTheme.typography.headlineSmall)
                    Text("Nodo voluntario Tier 0. No lee contactos, archivos ni credenciales.")
                    Text("Pantalla: $screen")
                    listOf(
                        "welcome" to "1 Bienvenida",
                        "consent" to "2 Consentimiento",
                        "pair" to "3 Emparejar (pegar payload, sin cámara)",
                        "status" to "4 Estado",
                        "beings" to "5 Beings",
                        "experiment" to "6 Experimento",
                        "memory" to "7 Memoria",
                        "security" to "8 Seguridad",
                        "logs" to "9 Logs",
                        "about" to "10 Acerca de",
                    ).forEach { (id, label) ->
                        Button(onClick = { screen = id }) { Text(label) }
                    }
                    Text(log)
                    Button(onClick = {
                        val result = CreatureTier0.run(seed = 7, ticks = 5, beingId = "being-1")
                        log = "engine=${result["engine"]} state=${result["final_state"]} events=${result["events"]}"
                        context.startForegroundService(Intent(context, NodeForegroundService::class.java))
                    }) { Text("Iniciar experimento Tier 0") }
                    Button(onClick = {
                        context.startService(
                            Intent(context, NodeForegroundService::class.java).setAction(NodeForegroundService.ACTION_STOP)
                        )
                        log = "STOP NEXO NODE"
                    }) { Text("STOP NEXO NODE") }
                }
            }
        }
    }
}
