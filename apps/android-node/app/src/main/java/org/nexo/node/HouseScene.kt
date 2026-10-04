package org.nexo.node

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import org.json.JSONObject

/** Same 160x120 house as the PC central. Phones and PCs are pixels. */
@Composable
fun HouseScene(state: JSONObject?, highlight: String, modifier: Modifier = Modifier) {
    Canvas(modifier.fillMaxWidth().aspectRatio(160f / 120f)) {
        val s = size.width / 160f
        fun px(x: Int, y: Int, w: Int, h: Int, color: Color) {
            drawRect(color, Offset(x * s, y * s), Size(w * s, h * s))
        }
        px(0, 0, 160, 20, Color(0xFF2A2420))
        val cap = ((state?.optInt("capacity") ?: 0) / 6).coerceIn(0, 16)
        for (i in 0 until 16) {
            val lit = i < cap
            px(8 + i * 9, 6, 6, 6, if (lit) Color(0xFFC46A32) else Color(0xFF5C5148))
            if (lit && i + 1 < cap) px(14 + i * 9, 8, 3, 2, Color(0xFFE7C39A))
        }
        px(0, 20, 160, 50, Color(0xFFE4D3BF))
        px(0, 70, 160, 50, Color(0xFF8D6244))
        px(138, 36, 12, 28, Color(0xFF5C3D2E))
        px(140, 38, 8, 24, Color(0xFF8E4A3A))
        px(96, 48, 6, 4, Color(0xFFE7C39A))
        px(98, 52, 2, 8, Color(0xFF5C3D2E))
        px(10, 28, 28, 20, Color(0xFF5C3D2E))
        px(12, 30, 10, 7, Color(0xFF9EC4D4))
        px(24, 30, 10, 7, Color(0xFF9EC4D4))
        px(8, 74, 28, 12, Color(0xFF5C3D2E))
        px(18, 76, 16, 8, Color(0xFF8E4A3A))
        px(62, 96, 28, 10, Color(0xFFA33B32))
        px(142, 68, 6, 5, Color(0xFF5C3D2E))
        px(141, 62, 8, 6, Color(0xFF3F6B4A))

        val nodes = state?.optJSONArray("nodes")
        val byId = mutableMapOf<String, JSONObject>()
        if (nodes != null) {
            for (i in 0 until nodes.length()) {
                val node = nodes.getJSONObject(i)
                byId[node.optString("id")] = node
            }
        }
        val links = state?.optJSONArray("connections")
        if (links != null) {
            for (i in 0 until links.length()) {
                val link = links.getJSONObject(i)
                val a = byId[link.optString("a")] ?: continue
                val b = byId[link.optString("b")] ?: continue
                dash(a.optInt("x") + 6, a.optInt("y") + 6, b.optInt("x") + 6, b.optInt("y") + 6, s)
            }
        }
        byId.values.forEach { node ->
            val x = node.optInt("x")
            val y = node.optInt("y")
            val on = node.optBoolean("online")
            if (node.optString("kind") == "phone") {
                px(x, y, 8, 14, if (on) Color(0xFF241F1B) else Color(0xFF8A8176))
                px(x + 1, y + 1, 6, 9, if (on) Color(0xFF9EC4D4) else Color(0xFFD9D0C3))
                if (on) {
                    px(x + 2, y + 3, 1, 1, Color(0xFF1C1915))
                    px(x + 5, y + 3, 1, 1, Color(0xFF1C1915))
                }
            } else {
                px(x - 2, y + 8, 16, 3, Color(0xFF5C3D2E))
                px(x, y, 12, 8, if (on) Color(0xFF1C1915) else Color(0xFF8A8176))
                px(x + 1, y + 1, 10, 5, if (on) Color(0xFF3F6B4A) else Color(0xFFD9D0C3))
            }
            if (node.optString("id") == highlight) {
                drawRect(
                    Color(0xFFB4532A),
                    Offset((x - 2) * s, (y - 2) * s),
                    Size(16 * s, 18 * s),
                    style = androidx.compose.ui.graphics.drawscope.Stroke(2f),
                )
            }
        }
        val pose = state?.optString("pose") ?: "idle"
        px(73, 86, 6, 2, Color(0xFF3A2A22))
        px(73, 88, 6, 6, Color(0xFFE8C4A4))
        px(74, 90, 1, 1, Color(0xFF1C1915))
        px(77, 90, 1, 1, Color(0xFF1C1915))
        px(73, 94, 6, 6, Color(0xFFB4532A))
        val armY = if (pose == "wave") 90 else 95
        px(79, armY, 1, 4, Color(0xFFE8C4A4))
        px(74, 100, 2, 4, Color(0xFF3A2A22))
        px(76, 100, 2, 4, Color(0xFF3A2A22))
    }
}

private fun androidx.compose.ui.graphics.drawscope.DrawScope.dash(x0: Int, y0: Int, x1: Int, y1: Int, scale: Float) {
    for (i in 0..12 step 2) {
        val t = i / 12f
        drawRect(
            Color(0xFF3F6B4A),
            Offset((x0 + (x1 - x0) * t) * scale, (y0 + (y1 - y0) * t) * scale),
            Size(2f * scale, 2f * scale),
        )
    }
}
