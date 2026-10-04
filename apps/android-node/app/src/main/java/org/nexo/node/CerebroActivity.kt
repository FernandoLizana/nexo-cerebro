package org.nexo.node

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme

/** Android phone in the house. It teaches the central and crosses ideas with the other nodes. */
class CerebroActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        PresenceClient.applyLabIntentExtras(this, intent)
        val autoGreet = intent?.getBooleanExtra(PresenceClient.EXTRA_AUTO_GREET, false) == true
        setContent {
            MaterialTheme {
                PresenceHome(
                    title = "NEXO Cerebro",
                    source = "android-cerebro",
                    blurb = "Un celular en la casa. Aprende libre y cruza ideas con los otros nodos.",
                    autoGreetOnStart = autoGreet,
                )
            }
        }
    }
}
