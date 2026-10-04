package org.nexo.node

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class CreatureTier0Test {
    @Test
    fun seed7MatchesPythonVector() {
        val result = CreatureTier0.run(seed = 7, ticks = 5, beingId = "being-1")
        assertEquals("FLEE", result["final_state"])
        assertEquals(listOf("1:FLEE", "2:FLEE", "3:FLEE", "4:REST", "5:FLEE"), result["events"])
        assertEquals(630, result["energy"])
        assertEquals(0, result["fear"])
        assertEquals(false, result["llm_used"])
    }

    @Test
    fun rejectsShellAndUnknownJobs() {
        val declared = setOf("RUN_CREATURE_SIMULATION")
        assertEquals("forbidden job type: EXECUTE_SHELL", MobileProtocol.jobAllowed("EXECUTE_SHELL", declared))
        assertEquals(
            "job type not allowlisted for mobile tier 0: RUN_BROWSERWORLD_EXPERIMENT",
            MobileProtocol.jobAllowed("RUN_BROWSERWORLD_EXPERIMENT", declared),
        )
        assertNull(MobileProtocol.jobAllowed("STOP_EXPERIMENT", declared))
    }
}
