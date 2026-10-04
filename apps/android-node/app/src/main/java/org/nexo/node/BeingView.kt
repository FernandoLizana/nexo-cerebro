package org.nexo.node

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.unit.dp

/** A breathing figure. Pose comes from the central hub: wave, look, nod, speak. */
@Composable
fun BeingView(pose: String, modifier: Modifier = Modifier) {
    val breath by rememberInfiniteTransition(label = "breath").animateFloat(
        initialValue = 0.98f,
        targetValue = 1.03f,
        animationSpec = infiniteRepeatable(tween(1600, easing = LinearEasing), RepeatMode.Reverse),
        label = "breathScale",
    )
    Canvas(modifier.fillMaxWidth().height(280.dp)) {
        val cx = size.width / 2f
        val ink = Color(0xFF1C1915)
        val skin = Color(0xFFF0D2B8)
        val cloth = Color(0xFFEFE6DA)
        scale(breath, breath, pivot = Offset(cx, size.height * 0.45f)) {
            val nod = if (pose == "nod") 8f else 0f
            rotate(nod, Offset(cx, 90f)) {
                drawOval(skin, Offset(cx - 46f, 40f), Size(92f, 104f))
                drawOval(ink, Offset(cx - 46f, 40f), Size(92f, 104f), style = Stroke(3f))
                drawCircle(ink, 5f, Offset(cx - 16f, 88f))
                drawCircle(ink, 5f, Offset(cx + 16f, 88f))
                val mouth = if (pose == "speak") 10f else 4f
                drawArc(ink, 20f, 140f, false, Offset(cx - 18f, 100f), Size(36f, mouth * 3), style = Stroke(3f))
            }
            drawOval(cloth, Offset(cx - 70f, 150f), Size(140f, 160f))
            drawOval(ink, Offset(cx - 70f, 150f), Size(140f, 160f), style = Stroke(3f))
            val armY = if (pose == "wave") 80f else 210f
            drawLine(ink, Offset(cx + 68f, 180f), Offset(cx + 110f, armY), strokeWidth = 8f)
        }
    }
}
