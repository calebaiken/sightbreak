# Independent three-agent integration review

Reviewed combined source `d5ff8da85c9c1122676efdcab12502064a517657` against PR11 `11573e587f13dfd832613a0c09dbc615f46d3461` and frozen Claude graphics `ed8575454452d8f67c006814a1917fa6cc24fb46`. Read-only source review and isolated Godot 4.7.2 probes. No source edits, cherry-picks, wholesale replacements, or GitHub posts by this reviewer.

## Acceptance decision

**Accept the shared-file integration and preserved network/authority boundary within the evidence below. Do not accept the complete combined milestone yet:** the frozen AI regression fails its audible-shot case, and fresh native artifacts have not been exported/inspected by this reviewer. The primary agent owns the wider suite and source-owner handoff. This review does not claim new physical-device, actual-account-service, or full export acceptance.

## Shared file and authority proof

`source-proof.json` records exact comparisons. `match.gd` adds/removes no methods, keeps identical ordered RPC declarations and protocol 6, and changes exactly seven methods: `_begin_round`, `_bot_input`, `_cover_position`, `_damaged`, `_eliminated`, `_nearest_defender`, `_reset_bot_state`. All changes are AI delegation/state hooks or AI weapon selection. Called SBBotAI methods exist in the integrated module; actor `weapon`, `smoke`, and `grenade` input fields use existing actor authority paths. No nonexistent AI API is called by the adapters.

Every file in `game/scripts/network/` and `server/` is byte-identical to PR11. Match admission, ticket inspect-before-consume capacity reservation, bounded peer lifecycle, retry token handling, result payload and submission gates, private recipient snapshots, and input/reconciliation code are unchanged. Client prediction remains opt-in through the unchanged configure method; snapshot and welcome call sites retain recipient-specific privacy.

Actor `tick_authority`, reload/equip/loadout/purchase, firing/hit trace, damage, and snapshot/apply methods are byte-identical to PR11. Compared with frozen Claude graphics, actor differs only in movement constants referencing SBMovementStep and replacing the inline movement block with `SBMovementStep.advance(self, input_state, delta)`. The reviewed integration preserves Claude's visual work without importing its earlier authority implementation.

## Independent runtime checks

| Probe | Result |
| --- | --- |
| State privacy | 55 checks, 0 failures |
| Movement prediction | 725 checks, 0 failures; max error 0.075834 m |
| Input stream | 17 checks, 0 failures |
| Peer lifecycle | 16 checks, 0 failures |
| Reconnect policy | 21 checks, 0 failures |
| Independent reconnect review | 24 checks, 0 failures with network enabled |
| Result outbox | 9 checks, 0 failures |
| Integrated actor lifecycle | 183 checks, 0 failures |
| Frozen AI regression | FAILED: non-carrier attacker should respond to nearby audible gunfire |

Logs are adjacent. The initial independent-reconnect run had sandbox-denied UDP socket engine errors despite reporting 24/0; it is not accepted as passing evidence. The separate `independent_reconnect_review_test-network.log` repeats the check with permitted networking and has no engine errors. Reconnect spy bridges test control flow, not PostgreSQL or external-service semantics.

The AI failure is concretely reproduced by the existing `_test_audio_and_damage_response`: attacker 2 stores a recent nearby enemy shot, then its carried-attacker plan picks split/flank destination and ignores auditory memory. The parent/AI reviewer is separately investigating the broader hearing, damage-turn and navigation behavior. This review makes no replacement edit and does not endorse frozen AI quality scores as runtime results.

## Export and test coverage

The validation runner registers AI regression and existing privacy/prediction/peer/reconnect/outbox/actor gates. `export_presets.cfg` uses all_resources for all three native targets and excludes `tests/*`; project global class cache registers SBBotAI, SBMovementStep, SBReloadAudio, SBReloadPhases and ConfirmSheet. Static configuration alone does not prove final artifact content.

At first review the export verifier omitted compiled-module assertions for the four new modules plus movement_step. Primary commit `d5ff8da` closes the omission. `export-resource-review.json` independently proves a complete synthetic resource list passes and removal of each individual module now fails with the specific missing-module assertion; the same omissions were incorrectly accepted by pre-fix verifier `10fdba0`. These are negative controls of verification logic, not actual resource inclusion evidence.

No Linux ELF, Android APK or iOS PCK exists in this worktree at this review point. Fresh three-target export, packed resource inspection, manifest/source binding, native smoke and Android/iOS metadata checks remain downstream gates.
