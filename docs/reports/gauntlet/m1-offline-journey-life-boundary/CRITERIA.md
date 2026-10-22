# Offline journey pause boundaries

Declared before implementation, 2026-10-22. Baseline controller/game source is
`4418161`, with the same game tree as frozen Windows CI `0ca125d` in run
[39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304).
The reference is that run's actual ordinary-journey actions, observations and
unchanged native captures, retained at `/workspace/reviews/native-ci-39719407304`.
No shipped-game visual comparison applies to this observer scheduling change.

The Windows journey failed after `07d-explicit-resume` because the actual local
player was dead. The living-player guard correctly rejected it. The primary HUD
analysis had resumed round 2 at elapsed 54.10 with 70.28 health, then the driver
immediately paused again to open settings. The settings capture shows 40 health;
the final generic Escape tap waits 0.3 seconds held and one second idle before
capturing resumed play. Native death is recorded at elapsed 54.533333. Native
and driver clocks differ; this is an ordering account, not an exact clock join.

Required checks:

- Preserve real OS controls, stock starts/seeds/rules, authoritative player life,
  focus and exact actor/round/weapon/ammunition context. Never inject state,
  teleport, grant invulnerability or alter time scale.
- Remove only avoidable live exposure created by the observer. Ordinary offline
  pause can span external OCR and field settings. Explicit resume must still be
  real native input, acknowledged by fresh game observation and actual pixels.
- Preserve rendered health/ammunition positives and actual menu/eliminated-image
  negatives. A dead player can never satisfy living HUD or focus acceptance.
- A necessary new life must come from bounded ordinary round flow and be
  recorded as such. A player dying during a required same-life transaction must
  fail that transaction; no retry loop may silently accept it.
- Keep the original 300-second whole-flow, 35-second second-live-round,
  160-second natural-round, 20-second OCR and other existing stage deadlines.
  New observation fences must fit their existing transaction budgets.
- Run actual exported Linux native input with raw actions, observer events and
  screenshots. Keep failed attempts, exact source/export identity and cleanup.
  Software rendering establishes observer behavior, not hardware performance.
- Recompute the actual Windows raw sequence and run both existing and candidate
  HUD readers on its real positive/negative frames. Exact Windows native rerun
  remains required after local work; Linux cannot satisfy that platform gate.
- Have a separate critic inspect source, raw controls, negatives, budgets and
  evidence before integration. The builder cannot approve this correction.

Largest known uncertainty: a lower-latency resume can still encounter legitimate
bot damage between authority acknowledgment and the screenshot. A change must
state that limit and must not weaken a guard to hide a gameplay failure.
