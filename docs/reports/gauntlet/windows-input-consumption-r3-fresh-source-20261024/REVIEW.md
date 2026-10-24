# R3 independent source review: REJECT

Frozen reader `342c3641ab2fccd1fc875c84188a8395a9b93a96` is better than rejected
R2 `86fe3cbe3f191b328c1e08bf8d5adc0a937e39b1`, but still accepts eleven newly
demonstrated source-impossible histories. Its reader SHA-256 is
`cb5897cb61d774499af0d4ac17252773ecaf91a954f75968f5eddebb26983eea`.
Criteria were committed and pushed as `b22c2790f9f960669832053bceb8f93ddb78e827`
before any test execution. This independent reviewer changed reports only.

R3 corrects seven false accepts and the unordered-header false rejection in the
final nine R2 controls. It retains all original 29 expectations. These are real
improvements, not source approval. The largest remaining gap is consistency
between cumulative stage history and the live peer/queue/actor state: earlier
work by peer A can qualify an impossible consumption by fresh peer B.

## Actual comparison and scope

All executions ran on CPU4 and imported the actual reader bytes. The full
checkout HEAD was the report-only preregistration commit; its complete tracked
non-document tree is identical to frozen `342c3641`. The separate initialized
depth-one checkout was at exact `342c3641`.

| Retained controls | Rejected R2 | Frozen R3 | Exact depth-one R3 |
| --- | ---: | ---: | ---: |
| Original independent 25 | 25/25 | 25/25 | 25/25 |
| Original supplemental 4 | 4/4 | 4/4 | 4/4 |
| Final unchanged additional 9 | 1/9 | 9/9 | 9/9 |
| New source controls 16 | 4/16 | 5/16 | 5/16 |
| Total expectations met | 34/54 | 43/54 | 43/54 |

R3 has eleven new false accepts and no false rejection in this bounded corpus.
R2 additionally rejects the valid reversed endpoint control, repeated once in
the old nine and once in the new controls. Both accept duplicate endpoints.
This was an attributed source comparison: hiding version identity would not
improve a correctness judgment based on exact source call order.

The maintained pure union passes 206 methods, including observation19,
identity6 and lifecycle7, with the same three Windows-only skips, both in the
full and initialized depth-one checkout. Shell syntax exits0. The pure runner
also retains unchanged platform-parser regression groups; this reviewer did
not investigate Mac file handling. A passing maintained suite does not detect
the eleven new failures or resolve its positive-fixture contradictions below.

The first new-control iteration was 40/49 with nine false accepts. It is
preserved in `full-r3-controls/` with `review_controls_r1_preserved.py`.
The second iteration normalizes the original simplified stream baseline, adds
an explicit baseline control and adds the coalesced peer pair. It is preserved
in `full-r3-controls-r2/` with `review_controls_r2_preserved.py` (42/52).
The final iteration adds a raw single-command projection falsifier and a valid
malformed→rejected→hidden-valid receive control; it is in `full-r3-controls-r3/`.
No original fixture or expectation was rewritten.

## Reproducible false accepts

Every following case expects `diagnostic_complete=false` and receives `true`,
with no errors, on frozen full and initialized depth-one R3. Exact input pairs,
source basis and actual results are in `full-r3-controls-r3/new-controls/<name>/`.

| Case directory | Source rule violated |
| --- | --- |
| `same_peer_second_live_generation` | One live peer binds actor4 at generation1, then generation2 binds actor5 without retirement. `peer_lifecycle.gd:12` rejects `peers.has(peer)`; `peer_disconnected` always emits, so forgetting this peer cannot be hidden. Reader membership at lines140–149 only distinguishes `(peer,generation)`. |
| `binding_counter_claims_hidden_lifecycle_event` | One direct `peer_bound` carries cumulative count2. Every binding lifecycle call increments and emits at `match.gd:1271,1298`; no omitted index or cap exists. |
| `emitted_reason_counter_does_not_increment` | A second emitted `authority_tick` retains its previous count. The emitter increments the reason counter before its filter; reader line130 merely forbids decreases. |
| `latest_accepted_deleted_without_reset` | `input_accepted` disappears from persistent `latest` at a later authority tick. The observer initializes once and only updates individual entries at `match.gd:1276`; the reader permits deletion. |
| `direct_accepted_has_empty_queue` | Acceptance carries queue0. `input_stream.gd:38` rejects empty staged intent, lines41–47 write a nonempty queue, and `_input_rpc` observes acceptance synchronously before any pop. |
| `consumed_ack_disagrees_with_command` | Consumed sequence21 carries ACK20. `input_stream.gd:83` assigns the returned sequence to acknowledged before observation. |
| `consumed_actor_projection_disagrees` | Consumed sequence21 carries actor input sequence22. `match.gd:279` assigns the popped command to that actor immediately before observing consumption. |
| `second_accept_without_receive_counter_increment` | Two accepts carry only one receive count. `_input_rpc:1066` calls receive before each acceptance, and its counter advances even when the row coalesces. The changed fire projection also requires a receive edge. |
| `accepted_latest_differs_from_synchronous_receive` | Direct accepted fire0 retains received fire1. Both observer calls receive the same `data` without an intervening await (`match.gd:1066,1078`). Compare packet header values excluding `wall_msec`, which may advance between calls. |
| `received_one_command_two_endpoints` | Count1 receive carries first21/last-9. `_native_input_packet` over one command necessarily projects equal endpoints, even for an invalid negative sequence; a nondictionary projects -1/-1. Prevalidation payload freedom does not permit an impossible observation projection. |
| `second_peer_pop_without_any_acceptance` | Fresh peer72 generation2 binds actor5 with an empty queue; its later pop claims sequence1 while global receive/accept counters remain1 from peer71. No hidden B acceptance exists because every acceptance increments those counters before coalescing. Reader lines168–169 reuse A's global lists. |

The paired `second_peer_coalesced_acceptance` expects and receives `true`.
Peer A's +X command and peer B's -X command share the same packet fire/reload/
moving aggregates. The per-reason receive/accept edges omit peer identity and
full movement, so B's rows can coalesce. Consumption includes full movement,
so B's row emits. The positive advances both cumulative counters to2 and
refreshes latest packet metadata; the negative leaves them at1. Requiring
direct receive/accept rows for every peer would reject the positive.

Other retained positive controls are `normalized_stream_control`,
`malformed_receive_then_coalesced_valid_receive`,
`valid_batch_endpoints_2_1` and `valid_batch_endpoints_1_1`. These are synthetic
projection controls, not acquired executions or a complete simulation model.
The rejection rests on direct deterministic contradictions in the listed fields.

## Historical positive fixtures conflict with source

The old38 bytes and expectations remain untouched in `original-fixtures/`,
with hashes in `fixture-manifest.json`. Their observed R3 pass count is a
historical regression result. It cannot be a requirement that a stricter reader
keep accepting every old positive while rejecting these same source contradictions.

Five positive independent25 cases (`coherent_independent_pipeline`,
`receive_wrong_epoch`, `receive_impossible_sequence`,
`consumption_outside_accepted_batch`, `client_send_epoch_disagrees_with_authority`)
and additional9 `coherent_control` have queue0 at direct acceptance and neutral
actor input at direct consumption. `consumption_outside_accepted_batch` also has
consumed sequence22 with ACK21. The final additional9 unordered case corrects
queue, ACK and consumed actor fields and does not have these contradictions.
`fixture-adjudication.json` records the exact detected contradictions by case.

The old `receive_impossible_sequence` also has count1 first21/last-9, which the
projection cannot emit. Likewise maintained identity test
`test_receive_keeps_malformed_prevalidation_payload_as_observation` changes count1
to first-1/last-9. A valid prevalidation control can use first=last=-9 and epoch-1,
then account for rejection and a later valid receive. Do not confuse accepting
malformed payload observations with accepting impossible projected metadata.

The maintained `test_input_consumption_observation.py:declared_rows()` additionally
starts `latest={}` on each row. The source keeps `diagnostic.latest` across rows.
It omits welcome latest metadata, has queue0 after acceptance, and gives the
consumed actor neutral sequence-1 despite consumed sequence1/firetrue. Lifecycle
and identity suites inherit this simplified fixture. Its assertions must remain
preserved as historical methods, but its positive fixture data requires an
explicitly preregistered source correction before stronger checks can pass.

For its count1 sequence1 baseline, source-supported replacements are:

- Retain each prior latest entry and timestamp until that stage next runs.
  Add welcome header metadata at `welcome_received`, and snapshot metadata when
  the applied-snapshot counter advances. Do not clear latest on attempt, peer
  change, or epoch reset; the observer has no such reset.
- Use first-connection stream ACK-1 before pop, queue1 at direct acceptance,
  then ACK1 and actor input `{sequence:1, fire:true, reload:false, move:[0,0]}`
  at consumption. Retain that actor input until a later source action changes it.
- Preserve the meanings of malformed prevalidation receive and sparse packet
  correlation controls. A malformed receive can be followed by a later valid
  receive/accept, but their cumulative counters and persistent latest metadata
  must reflect those calls. Do not relabel malformed incoming data as an invalid
  observation merely because authority later rejects it.

All future fixture corrections must be explicit new versions with a source-basis
map; retain the originals and original expected/actual outputs. Do not claim
contradictory original positives and new source checks both pass unchanged.

The synchronous `_input_rpc` also supports a useful count relation without
inventing packet identity: with R=`input_received`, A=`input_accepted`,
J=`input_stream_rejected`, an emitted receive row has R=A+J+1; other emitted
rows have R=A+J. Gate/decode rejection does not enter R. There is no await in
this body, and counters advance before coalescing. This is source guidance for
the next preregistration, not an implemented correction or additional test result.

Do not reject every unknown/repeated disconnect: `_service_peers` explicitly
calls `_peer_disconnected` after requesting transport disconnect; a later
transport callback may observe the already-forgotten peer with generation-1.
The current review does not impose a false exact-one-disconnect assumption.

## Provenance, coverage and unresolved scope

`full-source-bindings.json` and `depth-one-source-bindings.json` bind the entire
511-path tracked non-document union (all paths except `docs/`), including modes,
dotfiles, workflows, server and game. All512 unique source objects are available;
476 checked-out paths match exact object hashes and modes. The35 sparse omissions
retain exact tree object IDs and modes. The only R2→R3 non-document changes are
the analyzer and new lifecycle test. Runtime hooks, controller, transport,
authority and game source are unchanged. Source status is clean.

`depth-one-setup.json` records an initialized index (`read-tree -mu HEAD`,
`update-index --refresh`), clean status, shallow=true and commit_count1 at frozen
source. Its explicit local object alternate is `/workspace/sightbreak/.git/objects`.
This is not a self-contained clone or independent object-closure proof. No
full-blob clone was made. The only initial setup/read failure was an incorrect
`game/scripts/match.gd` search path; the actual path is
`game/scripts/gameplay/match.gd`. No test was skipped because of it.

`builder-additional-nine-original-results.json` preserves the builder artifact
whose static `candidate` says `86fe3cbe` while `checkout_head` says `342c3641`.
The analyzer hash matches frozen R3, and independent exact-source replay gets
9/9. This is an artifact header defect, not evidence that R2 passed those nine.
The exact builder rig and pure runner are preserved without editing them.

The old untraced Windows logs still return incomplete in the original25 replay.
No terminal capture receipt or end-to-end acquisition coverage follows from
`diagnostic_complete`; first/last packet projections do not expose full batches.
No original disconnect cause, observed native execution, physical latency,
gameplay or full release criterion is accepted. No Godot/native/CI/dispatch,
process inspection, production runtime change or Mac file-handling review ran.

Reproduce from this report directory's parent checkout on CPU4:

```sh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r3-fresh-source-20261024/review_controls.py --source . --output /tmp/r3-reader-fresh-output
```

Expected exit1 retains the eleven false accepts. Existing output paths are refused.
The committed execution receipts list actual commands and exit codes; use a new
output path for every replay. Source acceptance remains REJECTED until a new
offline reader correction and corrected source-faithful fixtures receive fresh
independent review.
