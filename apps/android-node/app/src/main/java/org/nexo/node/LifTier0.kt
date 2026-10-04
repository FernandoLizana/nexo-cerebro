package org.nexo.node

/**
 * Integer LIF matching protocols/lif/tier0.py.
 * Not Brian 2. Silence zeros outgoing weights only.
 */
object LifTier0 {
    const val ENGINE = "nexo-lif-tier0-v1"
    private const val V0 = -520
    private const val VRST = -520
    private const val VTH = -450
    private const val TM = 20
    private const val TAU = 5
    private const val DELAY = 2
    private const val RFC = 2
    private const val W_SYN = 80
    private const val DRIVE_KICK = 688

    private fun truncDiv(num: Int, den: Int): Int {
        if (den == 0) return 0
        return num / den
    }

    fun run(
        n: Int,
        edges: List<Triple<Int, Int, Int>>,
        ticks: Int,
        drive: Set<Int> = emptySet(),
        silence: Set<Int> = emptySet(),
        driveEvery: Int = 4,
    ): Map<String, Any> {
        require(n in 1..32)
        require(ticks in 1..200)
        val clean = edges.take(128).mapNotNull { (pre, post, count) ->
            val c = count.coerceIn(-12, 12)
            if (pre < 0 || post < 0 || pre >= n || post >= n || pre == post || c == 0) null
            else Triple(pre, post, c)
        }
        val v = IntArray(n) { V0 }
        val g = IntArray(n)
        val rfc = IntArray(n)
        val counts = IntArray(n)
        val spikes = mutableListOf<String>()
        val due = mutableListOf<Triple<Int, Int, Int>>()
        for (tick in 1..ticks) {
            val kept = mutableListOf<Triple<Int, Int, Int>>()
            for ((whenTick, post, delta) in due) {
                if (whenTick == tick) g[post] += delta
                else if (whenTick > tick) kept.add(Triple(whenTick, post, delta))
            }
            due.clear()
            due.addAll(kept)
            for (i in 0 until n) {
                if (rfc[i] > 0) {
                    rfc[i] -= 1
                    continue
                }
                if (i in drive && tick % driveEvery == 0) v[i] += DRIVE_KICK
                g[i] -= truncDiv(g[i], TAU)
                v[i] += truncDiv(V0 - v[i] + g[i], TM)
                if (v[i] > VTH) {
                    spikes.add("$tick:$i")
                    counts[i] += 1
                    v[i] = VRST
                    g[i] = 0
                    rfc[i] = RFC
                    if (i !in silence) {
                        for ((pre, post, count) in clean) {
                            if (pre == i) due.add(Triple(tick + DELAY, post, count * W_SYN))
                        }
                    }
                }
            }
        }
        return mapOf(
            "engine" to ENGINE,
            "spikes" to spikes,
            "rates_per_ks" to counts.map { it * 1000 / ticks },
            "spike_count" to spikes.size,
        )
    }

    fun golden(): Map<String, Any> = run(
        n = 4,
        edges = listOf(Triple(0, 1, 12), Triple(1, 2, 12), Triple(2, 3, 12)),
        ticks = 40,
        drive = setOf(0),
    )
}
