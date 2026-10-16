# Combined preview conflict record

This is an isolated validation branch; main and source PR branches are untouched.

## Ancestry

- Main: `e67f2c86777d98d3cb3ad6bc7e851ef1826af26d`.
- Foundation PR1: `227d6c8245a75522b8144c8004de2a86d61b833b`.
- Networking PR8 (contains PRs3–7): `89c0e997c9f706d91b02e5ac412853c4d35cd112`.
- Their common ancestor: `77e0433166b71c9de1456ef8639ce125d1b92029`.
- Initial graphics PR2: `8c18357e3a8045599ea3a805c115c5bebc76f97b`; already contains PR1 227d6c8.

`da9e687` merges the complete networking stack into the corrected foundation with no content conflict. `e896c81` merges graphics; one content conflict occurs at actor.gd constant declarations.

## Resolution

Keep Claude's `ViewmodelShading` preload. Keep Codex's `SBMovementStep` aliases for WALK_SPEED, CROUCH_SPEED and GRAVITY (same numeric values5.1,2.5,22). Preserve the movement delegation in `tick_authority`, every presentation field and the complete Claude `tick_visual`, attachments, cosmetic shader binding, skeleton and animation ownership.

Relative to graphics8c18357, actor.gd changes only three movement aliases and replacement of the existing movement block with `SBMovementStep.advance`. No weapon timing, hit-volume, ammunition, recoil or animation rules were replaced. `scripts/validate.sh` merged automatically and contains every test from both sides, including weapon-art. No file was replaced wholesale.

## Integration policy

This aggregate is for preview validation, not a shortcut around review of each constituent PR. Merge authorization remains with the owner. Preserve the stack order and protocol5/client-server parity; lifecycle needs its backend ticket-inspection route, and durable rewards need the worker/launcher/backend together. Prediction remains opt-in; combat-history recording remains diagnostic and live rewind is disabled. Claude owns all asset/material/animation corrections.

## Refreshed heads

Graphics64ec598 was merged atd084e500 with no content conflict. Foundation98ff57c was then merged with no conflict; it changes only main.gd status layout, tests and evidence. Its new custom-layout regression is deliberately reported rather than silently changing Claude's UI. Final matrix4ae4e5c and export60cf125 contain both refreshed heads. The actor diff against64ec598 still contains only movement constants/delegation. No source branch was modified.

## Reliability refresh —2026-10-14

New isolated branch:`integration/sightbreak-reliability-refresh`, based on old
previewa6b913c. Old PR9 and all source branches remain intact.

- Foundation148760e: clean merge75cc20d.
- Graphics68251a0: merge8548d67. Only `docs/DEVELOPMENT_STATUS.md` conflicted:
  preserve the prior preview as historical evidence and Claude's updated branch
  status, without discarding either record. Actor presentation merged cleanly.
- UI2b2731a: clean merge38552d8, included for limited preview validation with
  independently reported UI acceptance failures still open.
- Reconnect correctionc14dbc0 (PR10): mergefd5f04a. Five probe hunks and one Python
  report hunk reconciled the already shared barrier with new occupancy/input-ACK
  diagnostics and a single pre-I/O freshness timestamp. `validate.sh` retains both
  outbox tests/worker tests and all six reconnect regressions. No whole-file choice.

`actor.gd` differs from exact Claude68251a0 only in the pre-existing Codex movement
aliases and delegation. `main.gd`, `weapon_model.gd`, meshes, materials, animation
and art sources retain Claude's implementations. `match.gd` differs from the
focused reconnect branch only in the existing diagnostic hit-history and durable
result-outbox hooks. Protocol6 matched clients/server required. Prediction remains
opt-in and live rewind disabled. Source PRs were neither edited nor merged.

## Three-agent checkpoint

Isolated branch `integration/sightbreak-three-agent-alpha` starts from verified PR11 `11573e5`, preserving that PR and every source branch. Frozen PR14 `d66e72c` merged with only validation inventory conflict; native Godot exposed published API/property mismatches. Narrow match adapters and protocol-6/physics test bindings are recorded in `9f730dc`. Attacker auditory response remains a failing source-owner regression.

PR2 `ed85754` merges at `0345a18`; only status/validation conflicts preserve both records/suites. Actor presentation stays byte-identical to Claude except existing movement constants and SBMovementStep delegation. PR12 `7e41de6` merges at `cad5c0c`, retaining both fixture drift and network lifecycle checks. PR13 `7dd0628` adds research only. Separate reviewed backend guard `228c382` is merged; native confirmation adds only captured `expected_price` to the existing receipt payload.

No network/server file changes from PR11. Protocol6 matched builds, prediction opt-in, live rewind disabled. See [three-agent report](../reports/THREE_AGENT_INTEGRATION_REPORT.md) for exact source trees, retained failures, artifacts and acceptance limits.
