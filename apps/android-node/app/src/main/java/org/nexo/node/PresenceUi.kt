package org.nexo.node

import android.content.Context
import android.content.pm.ApplicationInfo
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.util.Base64
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

object PresenceClient {
    private const val PREFS = "nexo_presence"
    private const val KEY_HUB = "hub_base_url"
    private const val KEY_TOKEN = "presence_token"
    const val PRESET_EMULATOR = "http://10.0.2.2:8770"
    const val PRESET_LOOPBACK = "http://127.0.0.1:8770"
    const val TOKEN_HEADER = "X-Nexo-Presence-Token"
    const val EXTRA_HUB_URL = "hub_url"
    const val EXTRA_PRESENCE_TOKEN = "presence_token"
    const val EXTRA_AUTO_GREET = "auto_greet"

    /** Prefer adb reverse (127.0.0.1); then emulator host alias. Debug only. */
    private val debugFallbacks = listOf(PRESET_LOOPBACK, PRESET_EMULATOR)

    /** Lab automation: adb am start --es hub_url ... --es presence_token ... --ez auto_greet true */
    fun applyLabIntentExtras(context: Context, intent: android.content.Intent?) {
        if (intent == null) return
        val hub = intent.getStringExtra(EXTRA_HUB_URL)?.trim().orEmpty()
        if (hub.isNotEmpty()) {
            setHubBaseUrl(context, hub)
        }
        val token = intent.getStringExtra(EXTRA_PRESENCE_TOKEN)?.trim().orEmpty()
        if (token.isNotEmpty()) {
            setPresenceToken(context, token)
        }
    }

    fun getHubBaseUrl(context: Context): String {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY_HUB, "")
            ?.trim()
            ?.trimEnd('/')
            ?: ""
    }

    fun setHubBaseUrl(context: Context, url: String) {
        val cleaned = url.trim().trimEnd('/')
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_HUB, cleaned)
            .apply()
    }

    fun getPresenceToken(context: Context): String {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY_TOKEN, "")
            ?.trim()
            ?: ""
    }

    fun setPresenceToken(context: Context, token: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_TOKEN, token.trim())
            .apply()
    }

    private fun applyAuth(conn: HttpURLConnection, context: Context) {
        val token = getPresenceToken(context)
        if (token.isNotEmpty()) {
            conn.setRequestProperty(TOKEN_HEADER, token)
        }
    }

    private fun isDebuggable(context: Context): Boolean {
        return (context.applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0
    }

    /**
     * Prefer the user-configured hub URL. Emulator/loopback fallbacks apply
     * only on debuggable builds when no URL is set (or as secondary tries
     * after the configured URL fails).
     */
    fun hubCandidates(context: Context): List<String> {
        val configured = getHubBaseUrl(context)
        val out = linkedSetOf<String>()
        if (configured.isNotEmpty()) {
            out += configured
        }
        if (isDebuggable(context)) {
            for (fb in debugFallbacks) {
                out += fb
            }
        }
        return out.toList()
    }

    fun interact(context: Context, source: String, kind: String, text: String, onState: (JSONObject) -> Unit) {
        Executors.newSingleThreadExecutor().execute {
            val state = try {
                post(context, source, kind, text)
            } catch (exc: Exception) {
                JSONObject().put(
                    "speech",
                    "Sin central. Configurá la URL del hub (LAN o emulador). En el PC: python -m services.presence.hub",
                )
            }
            Handler(Looper.getMainLooper()).post { onState(state) }
        }
    }

    fun leaveMaterial(
        context: Context,
        source: String,
        name: String,
        bytes: ByteArray,
        note: String,
        onDone: (String) -> Unit,
    ) {
        Executors.newSingleThreadExecutor().execute {
            val speech = try {
                val body = JSONObject()
                    .put("source", source)
                    .put("name", name)
                    .put("note", note)
                    .put("data_b64", Base64.encodeToString(bytes, Base64.NO_WRAP))
                val json = postRaw(context, "/v1/material", body)
                if (json.optBoolean("ok")) "Quedó en el nodo. La central lo toma si quiere, o al dormir."
                else json.optString("error", "no se guardó")
            } catch (exc: Exception) {
                "Sin central. Configurá la URL del hub (LAN o emulador). En el PC: python -m services.presence.hub"
            }
            Handler(Looper.getMainLooper()).post { onDone(speech) }
        }
    }

    fun poll(context: Context, onState: (JSONObject) -> Unit) {
        Executors.newSingleThreadExecutor().execute {
            val state = try {
                get(context, "/v1/state")
            } catch (exc: Exception) {
                return@execute
            }
            Handler(Looper.getMainLooper()).post { onState(state) }
        }
    }

    private fun requireHubs(context: Context): List<String> {
        val hubs = hubCandidates(context)
        if (hubs.isEmpty()) {
            throw IllegalStateException(
                "Hub URL vacía. En un teléfono físico configurá la IP LAN del PC (o HTTPS).",
            )
        }
        return hubs
    }

    private fun post(context: Context, source: String, kind: String, text: String): JSONObject {
        var last: Exception? = null
        for (hub in requireHubs(context)) {
            try {
                return postOne(context, hub, source, kind, text)
            } catch (exc: Exception) {
                last = exc
            }
        }
        throw last ?: IllegalStateException("hub")
    }

    private fun postRaw(context: Context, path: String, body: JSONObject): JSONObject {
        var last: Exception? = null
        for (hub in requireHubs(context)) {
            try {
                val conn = URL("$hub$path").openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json")
                applyAuth(conn, context)
                conn.connectTimeout = 4000
                conn.readTimeout = 8000
                conn.outputStream.use { it.write(body.toString().toByteArray()) }
                val stream = if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream
                return JSONObject(stream.bufferedReader().readText())
            } catch (exc: Exception) {
                last = exc
            }
        }
        throw last ?: IllegalStateException("hub")
    }

    private fun get(context: Context, path: String): JSONObject {
        var last: Exception? = null
        for (hub in requireHubs(context)) {
            try {
                val conn = URL("$hub$path").openConnection() as HttpURLConnection
                conn.connectTimeout = 2500
                conn.readTimeout = 2500
                return JSONObject(conn.inputStream.bufferedReader().readText())
            } catch (exc: Exception) {
                last = exc
            }
        }
        throw last ?: IllegalStateException("hub")
    }

    private fun postOne(
        context: Context,
        hub: String,
        source: String,
        kind: String,
        text: String,
    ): JSONObject {
        val conn = URL("$hub/v1/interact").openConnection() as HttpURLConnection
        conn.requestMethod = "POST"
        conn.doOutput = true
        conn.setRequestProperty("Content-Type", "application/json")
        applyAuth(conn, context)
        conn.connectTimeout = 2500
        conn.readTimeout = 2500
        val body = JSONObject()
            .put("source", source)
            .put("kind", kind)
            .put("text", text)
        conn.outputStream.use { it.write(body.toString().toByteArray()) }
        val code = conn.responseCode
        val stream = if (code in 200..299) conn.inputStream else conn.errorStream
        val raw = stream.bufferedReader().readText()
        if (code !in 200..299) {
            throw IllegalStateException("hub HTTP $code: ${raw.take(120)}")
        }
        val json = JSONObject(raw)
        return json.optJSONObject("state") ?: json
    }
}

@Composable
fun PresenceHome(
    title: String,
    source: String,
    blurb: String,
    onStop: (() -> Unit)? = null,
    autoGreetOnStart: Boolean = false,
) {
    var state by remember { mutableStateOf<JSONObject?>(null) }
    var note by remember { mutableStateOf("") }
    var shelf by remember { mutableStateOf("") }
    val context = LocalContext.current
    var hubUrl by remember { mutableStateOf(PresenceClient.getHubBaseUrl(context)) }
    var presenceToken by remember { mutableStateOf(PresenceClient.getPresenceToken(context)) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri == null) return@rememberLauncherForActivityResult
        val queried = context.contentResolver.query(uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null)
        val display = queried?.use { if (it.moveToFirst()) it.getString(0) else null }
        val rawName = display ?: uri.lastPathSegment?.substringAfterLast('/') ?: "nota.txt"
        val name = if ('.' in rawName) rawName else "nota.txt"
        val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() } ?: return@rememberLauncherForActivityResult
        if (bytes.size > 2_500_000) {
            shelf = "Demasiado grande. Máximo 2.5 MB."
            return@rememberLauncherForActivityResult
        }
        PresenceClient.leaveMaterial(context, source, name, bytes, note) { shelf = it }
    }
    DisposableEffect(hubUrl) {
        val handler = Handler(Looper.getMainLooper())
        val tick = object : Runnable {
            override fun run() {
                PresenceClient.poll(context) { state = it }
                handler.postDelayed(this, 1200)
            }
        }
        handler.post(tick)
        if (autoGreetOnStart) {
            handler.postDelayed({
                PresenceClient.interact(context, source, "GREET", "hola auto lab") { state = it }
            }, 800)
        }
        onDispose { handler.removeCallbacksAndMessages(null) }
    }
    val paper = Color(0xFFF4EFE6)
    Column(
        Modifier.fillMaxSize().background(paper).verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(title, style = MaterialTheme.typography.headlineSmall)
        Text(blurb)
        OutlinedTextField(
            value = hubUrl,
            onValueChange = {
                hubUrl = it
                PresenceClient.setHubBaseUrl(context, it)
            },
            label = { Text("URL del hub (vacío = sin forzar)") },
            placeholder = { Text("http://192.168.x.x:8770") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = presenceToken,
            onValueChange = {
                presenceToken = it
                PresenceClient.setPresenceToken(context, it)
            },
            label = { Text("Token del hub (POSTs)") },
            placeholder = { Text("desde data/presence_hub/token.txt") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            OutlinedButton(
                onClick = {
                    hubUrl = PresenceClient.PRESET_LOOPBACK
                    PresenceClient.setHubBaseUrl(context, hubUrl)
                },
            ) { Text("127.0.0.1 (adb reverse)") }
            OutlinedButton(
                onClick = {
                    hubUrl = PresenceClient.PRESET_EMULATOR
                    PresenceClient.setHubBaseUrl(context, hubUrl)
                },
            ) { Text("Emulador 10.0.2.2") }
            OutlinedButton(
                onClick = {
                    if (hubUrl.isBlank() || hubUrl.startsWith("http://10.0.2.2") || hubUrl.startsWith("http://127.0.0.1")) {
                        hubUrl = "http://192.168.1.1:8770"
                    }
                    PresenceClient.setHubBaseUrl(context, hubUrl)
                },
            ) { Text("Plantilla LAN") }
        }
        Text(
            "Teléfono físico: IP LAN del PC + token, o HTTPS vía lab_gateway. Cleartext solo lab.",
            style = MaterialTheme.typography.bodySmall,
        )
        HouseScene(state, source)
        Text("Capa neuronal · capacidad ${state?.optInt("capacity") ?: 8}")
        Text(state?.optJSONObject("lif")?.let { "LIF ${it.optString("engine")} tasas ${it.optJSONArray("rates_per_ks")}" } ?: "LIF esperando una interacción")
        Text(state?.optString("speech") ?: "En casa, esperando a los otros nodos.")
        val idea = state?.optJSONArray("ideas")?.let { if (it.length() == 0) "" else it.getJSONObject(it.length() - 1).optString("text") } ?: ""
        if (idea.isNotEmpty()) Text("Idea de los nodos: $idea")
        if (shelf.isNotEmpty()) Text(shelf)
        Button(onClick = { picker.launch("*/*") }) { Text("Dejar texto, PDF o imagen") }
        OutlinedTextField(value = note, onValueChange = { note = it }, label = { Text("aprendizaje libre") }, modifier = Modifier.fillMaxWidth())
        Button(onClick = { PresenceClient.interact(context, source, "GREET", note) { state = it } }) { Text("Saludar") }
        Button(onClick = { PresenceClient.interact(context, source, "OBSERVE", note.ifBlank { "un gesto en la casa" }) { state = it } }) { Text("Observar") }
        Button(onClick = { PresenceClient.interact(context, source, "TEACH", note.ifBlank { "un silencio" }) { state = it } }) { Text("Enseñar") }
        Button(onClick = { PresenceClient.interact(context, source, "ASK", note.ifBlank { "qué cruzaron" }) { state = it } }) { Text("Preguntar") }
        if (onStop != null) Button(onClick = onStop) { Text("STOP NEXO NODE") }
    }
}
