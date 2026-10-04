package org.nexo.node

import org.junit.Assert.assertEquals
import org.junit.Test

class LifTier0Test {
    @Test
    fun goldenMatchesPython() {
        val result = LifTier0.golden()
        assertEquals("nexo-lif-tier0-v1", result["engine"])
        assertEquals(
            listOf(
                "4:0", "8:0", "8:1", "12:0", "12:2", "13:1", "16:0", "16:3", "17:2", "18:1",
                "20:0", "21:3", "22:2", "24:0", "24:1", "26:3", "28:0", "28:2", "29:1", "32:0",
                "32:3", "33:2", "34:1", "36:0", "37:3", "38:2", "40:0", "40:1",
            ),
            result["spikes"],
        )
        assertEquals(listOf(250, 175, 150, 125), result["rates_per_ks"])
    }

    @Test
    fun silenceCutsOutgoingOnly() {
        val cut = LifTier0.run(
            n = 4,
            edges = listOf(Triple(0, 1, 12), Triple(1, 2, 12), Triple(2, 3, 12)),
            ticks = 40,
            drive = setOf(0),
            silence = setOf(1),
        )
        assertEquals(listOf(250, 175, 0, 0), cut["rates_per_ks"])
    }
}
