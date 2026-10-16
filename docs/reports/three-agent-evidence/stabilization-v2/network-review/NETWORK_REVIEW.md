# Independent network cleanup and marketplace preservation review

## Scope and source identity

The reviewed original game is frozen at `a939f1e7e0c32a5ef7ffbad0a714beb3af365259` in the detached `frozen/` worktree. All native runs used official Godot `4.7.2.stable.official.ed1daf0bf`, headless, with the Dummy audio driver. The `godot` executable on PATH is 4.6.3 and was deliberately not used. Network probes used only reserved ports 36071–36085. Source and shipping branches were not edited by this reviewer; custom drivers and logs live in this review directory.

## Source-bound finding: the nested warning is deferred audio cleanup

**The matched current/current client's exit warning is reproducible, but the leaked objects are a transient shot's `AudioStreamPlaybackWAV` and its referenced `AudioStreamWAV`, not an ENet peer, packet, SceneMultiplayer, actor, or scene node.** The stock probe frees its Match, awaits one process frame, and quits (`game/tests/protocol_client_probe.gd:45–47`). One process frame does not guarantee completion of the AudioServer mixer's deferred playback deletion.

The unchanged stock 15-second run joined and exited cleanly (`original-1/`). Its live round began at approximately 14.8 seconds, so that run did not reliably exercise active gunfire at exit. The unchanged stock 30-second run joined protocol 6 and leaked two objects (`original-30s/`). The historical five-object warning should remain preserved: the exact count depends on the sounds active at exit and is not a stable count of leaked network resources.

An independent 30-second instrumented reproduction (`instrumented-natural-1/client.log`) identified the exact owning path immediately before teardown:

| Item | Observed identity |
| --- | --- |
| Transient voice | `/root/Sightbreak/Match/@AudioStreamPlayer3D@3233`, node ID `214563820069`, `playing=true` |
| Voice's WAV | signed GDScript ID `-9223371909482146294`, unsigned ObjectDB ID `9223372164227405322` |
| Voice's playback | signed GDScript ID `-9223371822240624137`, unsigned ObjectDB ID `9223372251468927479` |
| Source cache | `SBActor._shot_streams['sidearm']` |

Both unsigned IDs match the two verbose leaked-object records exactly, each with reference count 1. The emitter is created in `Match._audible_shot_rpc` (`game/scripts/gameplay/match.gd:1051–1066`), assigned the cached weapon stream, and connected to `finished -> queue_free`. All actor shot/hurt/reload voices were inactive in this mapped reproduction. After `game.queue_free()` the probe verified that the Match was invalid and the active multiplayer peer was `OfflineMultiplayerPeer`; no transport object appeared in the ObjectDB leaks.

## Causal controls and narrow correction

A short controlled client probe creates one sidearm sound through the existing `_audible_shot_rpc` presentation method, allows 40 ms for playback to start, then uses the stock teardown. This is a presentation-only intervention in an external driver; no authoritative combat state or protocol traffic contract is changed.

| Control | Result |
| --- | --- |
| Forced sidearm, stock one-frame exit (`force-sidearm-1/`) | Two exact WAV/playback leaks |
| Stop voice and set `stream=null` before scene deletion (`force-sidearm-stop-null/`) | Same two-object warning |
| Stop voice before scene deletion (`force-sidearm-stop-only/`) | Same two-object warning |
| Close client peer before scene deletion (`force-sidearm-close/`) | Same two-object warning |
| Wait 0.3 seconds **after** deletion (`force-sidearm-drain/`) | Clean |
| Repeat that post-deletion wait (`force-sidearm-drain-repeat-2/`, `force-sidearm-drain-repeat-3/`) | Both clean; 3/3 forced drain runs total |
| Natural 30-second match, 0.3 seconds after deletion (`natural-drain-30s/`) | Clean, joined protocol 6 |

The reference-lifetime probe (`force-sidearm-track-refs/client.log:132–137`) provides direct evidence beyond simply observing clean logs. With only the review array and loop variable deliberately retaining the observed playback, its reference count remained 3 immediately after the Match was freed and at 6.9, 13.8, and 20.7 ms afterward. It dropped to 2 at 27.6 ms, showing release of an additional owner after scene deletion. Clearing the review references then allowed a clean exit.

This agrees with the official 4.7.2 engine source obtained by the independent audio reviewer: `AudioStreamPlayerInternal::NOTIFICATION_PREDELETE` requests playback stop and clears its own playback vector (`audio/engine-internal.cpp:111–116`); `AudioServer::stop_playback_stream` marks the mixer entry `FADE_OUT_TO_DELETION` (`audio/engine-server.cpp:1289–1319`); a later mixer pass removes it (`:534–538`). Immediate process exit can precede that pass. No engine terminal-pause-state defect has been established by these probes.

**Accepted narrow correction:** retain the existing summary and `game.queue_free(); await process_frame`, then `await create_timer(0.5).timeout` before `quit()` in the protocol client fixture. The primary agent's concrete diff was reviewed and contains only that documented post-result wait. It provides a conservative post-deletion mixer drain and changes no compatibility assertion, protocol version, runtime RPC, privacy entitlement, prediction behavior, rewind setting, ticket handling, or result-delivery behavior. The 0.3-second controls establish the causal effect; the proposed 0.5-second value leaves more shutdown margin. This is a fixture shutdown correction. This reproduction does not justify changing the runtime network lifecycle.

An earlier natural stop/null run (`instrumented-stop-null/`) also exited cleanly, but it had a different active voice at exit and is not treated as proof that stop/null alone fixes the warning. Similarly, clean forced rifle/actor-shot runs are retained and not used to erase the failing sidearm controls.

## Focused network regression evidence

Unchanged source `a939f1e`, separate native processes, all clean:

- Recipient privacy: **55 checks, 0 failures** (`state_privacy_test.log`).
- Snapshot buffer: **15 checks, 0 failures** (`snapshot_buffer_test.log`).
- Movement prediction: **725 checks, 0 failures**, maximum error 0.075834 m (`movement_prediction_test.log`).
- Peer lifecycle/capacity: **16 checks, 0 failures** (`peer_lifecycle_test.log`).

Commands/results and source identity are in `focused-network-tests.json`. These focused runs do not replace the primary agent's upcoming full frozen regression and eight-pair compatibility campaign.

## Marketplace consent preservation

The original marketplace guard was preserved. At `a939f1e`, backend app/models/tests/config are identical to the separately reviewed PR15 `228c382` implementation. The integrated native market confirmation sends `expected_price: price` from the same captured value used in the sheet (`game/scripts/ui/economy_ui.gd:1291`).

Independent real-PostgreSQL validation on the dedicated disposable database `sightbreak_stabilization_network_review_test` passed **61/61 tests** (`market-backend-baseline.log`). This includes strict supplied-price validation, higher/lower mismatch rejection without balance/item/listing/receipt mutation, authoritative fees and debits, concurrent identical receipts, exact replay after price/state change, changed-payload conflicts, pre-guard receipt hashes, legacy omission/null behavior, trade revisions, and transaction rollback. The only warning is the pre-existing Starlette/httpx deprecation warning.

`market-baseline.json` records Git blob IDs and SHA-256 checksums for 11 guard-related backend/native runtime and test files. `market-preservation-current.json` confirms every file is byte-identical at integration head `f259ab31a526cfa19b6d76c8e9d47b8a968defb7`. The final frozen integration head still requires a last preservation comparison; this report does not attribute the baseline execution to a future commit.

## Committed correction and later integration preservation

The narrow protocol fixture correction is now committed as `fb1e6459f3550216805fabfd07f3013d7dbe662f`. Independent inspection of that committed diff confirms exactly the reviewed comment and 0.5-second post-deletion wait, with no other protocol probe change. That fixture correction is accepted on the source review and controlled native evidence above.

A subsequent independent comparison at integration head `81434b43070c6e92125da8ef7c6b93c652a12266` again found **all 11 tracked marketplace files byte-identical** to `a939f1e`. `market-preservation-81434b4.json` records both SHA-256 values and the newer commit's Git blob IDs. The integration changed none of `game/scripts/network/`, the marketplace backend implementation, or the native economy UI/API files between those commits. This confirms preservation through that exact newer head without relabeling the 61-test baseline execution as a run against newer source. Further source commits should retain the same file comparison in the final campaign manifest.

## Final frozen campaign acceptance — aee6b73

**Independent final static review accepted:** frozen campaign source `aee6b7396928489662eb9917c7e403a1a00a21af` preserves all 11 marketplace files byte for byte against Git objects from the original execution baseline `a939f1e7e0c32a5ef7ffbad0a714beb3af365259`. Both SHA-256 values and Git blob IDs are recorded in `final-campaign-preservation-aee6b73.json`. The complete `backend/` tree is also identical (`67027b4fa17674ef067c84401af76eb1524419ac`), and the complete `game/scripts/network/` tree is identical (`e5f64b6d8de282dfd5149d8c70b43bbe083bab55`). No backend or engine process was run for this final comparison; the primary agent's full frozen campaign is separate.

The only change in `game/scripts/gameplay/match.gd` between those exact commits is the round-plan integration: the obsolete `select_round_plan(round_number, _rng)` assignment before the actor loop is replaced with `select_round_plan(self, 0)` after actor reset and purchase (`final:348`). Inspection of its final callee (`game/scripts/gameplay/bot_ai.gd:153–168`) confirms that it reads the round/carrier/arena and writes only the team AI `primary_site` and `target_site`; it grants no weapon, ammunition, utility, currency, inventory, or network entitlement. The existing `actor.reset_for_round`, `_reset_bot_state`, and authoritative `actor.buy_weapon` calls are unchanged (`final:343–347`). The complete actor and main scripts are byte-identical to the baseline.

All **13 RPC annotations and method signatures** in Match are identical. Protocol remains **6**. Transport/authentication, recipient snapshot generation, combat authority, opt-in prediction, and the absence of live rewind retain their existing implementations: the entire Match diff is the single round-plan call replacement, and the complete networking directory is unchanged. No authority or marketplace blocker was found in this final static comparison. The exact Match diff is retained as `final-match-authority.diff` and checksummed in the receipt.

Provenance clarification: the earlier `market-baseline.json` actually recorded repository head `d232b96704078b5b7e69c6428d3cbe8643c39581` after the branch advanced during the initial review, while native/backend executions remained in the detached `a939f1e` worktree. The final receipt independently reads both frozen commits using `git show`, verifies that all 11 earlier recorded hashes are also identical to the `a939f1e` Git objects, and records the distinction explicitly. This removes any ambiguity without changing the execution source or its original logs.
