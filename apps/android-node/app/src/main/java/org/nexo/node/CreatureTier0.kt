package org.nexo.node

/**
 * Integer FSM matching protocols/mobile/creature_tier0.py.
 * Not a port of the float Python CreatureEngine.
 */
object CreatureTier0 {
    private val transitions = mapOf(
        "IDLE" to setOf("FORAGE", "EXPLORE", "REST", "FLEE", "SOCIALIZE", "INSPECT", "IDLE"),
        "FORAGE" to setOf("EAT", "EXPLORE", "FLEE", "IDLE"),
        "EAT" to setOf("IDLE", "REST", "FLEE"),
        "REST" to setOf("IDLE", "EXPLORE", "FLEE"),
        "EXPLORE" to setOf("INSPECT", "FORAGE", "IDLE", "FLEE"),
        "FLEE" to setOf("IDLE", "REST"),
        "SOCIALIZE" to setOf("IDLE", "EXPLORE", "FLEE"),
        "INSPECT" to setOf("EXPLORE", "IDLE", "FLEE"),
    )
    private val actions = listOf("EAT", "EXPLORE", "FLEE", "FORAGE", "IDLE", "INSPECT", "REST", "SOCIALIZE")

    fun xorshift32(state: Long): Long {
        var x = state and 0xFFFFFFFFL
        if (x == 0L) x = 0x6D2B79F5L
        x = x xor ((x shl 13) and 0xFFFFFFFFL)
        x = x xor (x shr 17)
        x = x xor ((x shl 5) and 0xFFFFFFFFL)
        return x and 0xFFFFFFFFL
    }

    fun run(seed: Long, ticks: Int, beingId: String): Map<String, Any> {
        require(ticks in 1..200)
        var rng = seed and 0xFFFFFFFFL
        val drives = mutableMapOf(
            "hunger" to 300,
            "curiosity" to 500,
            "energy" to 700,
            "fear" to 200,
            "sociability" to 500,
            "exploration" to 500,
        )
        var fsm = "IDLE"
        val events = mutableListOf<String>()
        repeat(ticks) { index ->
            rng = xorshift32(rng)
            val draw = rng
            val cue = mapOf(
                "food" to ((draw and 1L) != 0L),
                "threat" to ((draw and 2L) != 0L),
                "agent" to ((draw and 4L) != 0L),
                "novel" to ((draw and 8L) != 0L),
            )
            var best: String? = null
            var bestScore = -10_000
            for (action in actions) {
                val allowed = transitions.getValue(fsm)
                if (action !in allowed && action != fsm) continue
                var score = drives[mapOf(
                    "FORAGE" to "hunger",
                    "EAT" to "hunger",
                    "REST" to "energy",
                    "EXPLORE" to "exploration",
                    "FLEE" to "fear",
                    "SOCIALIZE" to "sociability",
                    "INSPECT" to "curiosity",
                    "IDLE" to "energy",
                ).getValue(action)] ?: 0
                if (cue.getValue("threat") && action == "FLEE") score += 900
                if (cue.getValue("threat") && action in setOf("EAT", "SOCIALIZE", "REST")) score -= 800
                if (cue.getValue("food") && action in setOf("FORAGE", "EAT")) score += 550
                if (cue.getValue("agent") && action == "SOCIALIZE") score += 450
                if (cue.getValue("novel") && action == "INSPECT") score += 500
                if (action == "IDLE") score = 150
                if (best == null || score > bestScore || (score == bestScore && action < best)) {
                    best = action
                    bestScore = score
                }
            }
            fsm = best!!
            when (fsm) {
                "EAT" -> {
                    drives["hunger"] = (drives.getValue("hunger") - 120).coerceIn(0, 1000)
                    drives["energy"] = (drives.getValue("energy") + 20).coerceIn(0, 1000)
                }
                "FLEE" -> {
                    drives["fear"] = (drives.getValue("fear") - 80).coerceIn(0, 1000)
                    drives["energy"] = (drives.getValue("energy") - 40).coerceIn(0, 1000)
                }
                "REST" -> drives["energy"] = (drives.getValue("energy") + 90).coerceIn(0, 1000)
                "FORAGE" -> {
                    drives["hunger"] = (drives.getValue("hunger") + 40).coerceIn(0, 1000)
                    drives["energy"] = (drives.getValue("energy") - 15).coerceIn(0, 1000)
                }
                "EXPLORE" -> {
                    drives["exploration"] = (drives.getValue("exploration") - 10).coerceIn(0, 1000)
                    drives["energy"] = (drives.getValue("energy") - 10).coerceIn(0, 1000)
                }
            }
            if (events.size < 64) events += "${index + 1}:$fsm"
        }
        return mapOf(
            "engine" to MobileProtocol.ENGINE,
            "being_id" to beingId,
            "final_state" to fsm,
            "events" to events,
            "energy" to drives.getValue("energy"),
            "fear" to drives.getValue("fear"),
            "llm_used" to false,
        )
    }
}
