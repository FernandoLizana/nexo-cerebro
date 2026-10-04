# P8 — Transient Errors

`TRANSIENT_ERROR` / `NETWORK_LIKE_FAILURE` reject valid actions with recoverable errors.

NEXO decides retry strategy — **no automatic cognitive retry from environment**.

Parameters: `fail_attempts` — failures before success path proceeds.
