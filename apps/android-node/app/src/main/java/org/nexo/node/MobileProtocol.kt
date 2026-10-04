package org.nexo.node

/** mobile-v1 helpers shared with protocols/mobile on the PC. */
object MobileProtocol {
    const val VERSION = "mobile-v1"
    const val ENGINE = "creature-mobile-tier0-v1"

    val allowed = setOf(
        "RUN_CREATURE_SIMULATION",
        "RUN_TEXTWORLD_EXPERIMENT",
        "RUN_BEING_INTERACTION",
        "CREATE_BEING",
        "LIST_BEINGS",
        "GET_NODE_STATUS",
        "PAUSE_NODE",
        "RESUME_NODE",
        "STOP_EXPERIMENT",
    )
    val forbidden = setOf(
        "EXECUTE_SHELL",
        "INSTALL_PACKAGE",
        "OPEN_URL",
        "READ_PATH",
        "WRITE_PATH",
        "UPLOAD_FILE",
        "DOWNLOAD_FILE",
        "SCAN_NETWORK",
        "READ_CONTACTS",
        "READ_MESSAGES",
        "READ_LOCATION",
        "CAPTURE_AUDIO",
        "CAPTURE_CAMERA",
        "CAPTURE_SCREEN",
        "ACCESS_CLIPBOARD",
    )

    fun jobAllowed(jobType: String, declared: Set<String>): String? {
        if (jobType.isBlank()) return "empty job_type"
        if (jobType in forbidden) return "forbidden job type: $jobType"
        if (jobType !in allowed) return "job type not allowlisted for mobile tier 0: $jobType"
        if (jobType !in setOf("GET_NODE_STATUS", "PAUSE_NODE", "RESUME_NODE", "STOP_EXPERIMENT") && jobType !in declared) {
            return "node did not declare job: $jobType"
        }
        return null
    }
}
