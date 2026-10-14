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
