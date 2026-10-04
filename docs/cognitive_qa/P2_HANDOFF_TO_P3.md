# P2 → P3 handoff

P3 improves **perceptual fidelity** without rewriting BrowserWorld contract.

## From P2

- `BrowserSnapshot` / `BrowserElementSnapshot`
- Element registry (`web:e:NNNN` → locator)
- `BrowserWorld` lifecycle
- `action_mapper` / `ActionSchema` ids
- `PlaywrightDriver`
- Web Lab + trace log
- Selector secrecy tests

## P3 may add

- Perceptual modes: `DOM_FAST` (current), `HYBRID`, `VISION`
- Salience, clutter, viewport limits, attention budget
- Richer percept DTO (still not raw locators in core)

## Must keep passing

All P1 tests, v90 golden, P2 browser tests, `test_three_worlds_one_brain`.

## Do not in P3

Break `EnvironmentProtocol` method names or move locators into `ActionSchema` cognitive fields.
