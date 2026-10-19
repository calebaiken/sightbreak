# Network input freshness — bounded V3 correction

**Measured winner: the candidate enforces the existing silence and idle rules
when clients retransmit only acknowledged commands.** In the matched native
workload, baseline continued moving and retained the stale peer; candidate stopped
movement and retired the peer, then accepted fresh controls normally. Development
draft [PR20](https://github.com/calebaiken/sightbreak/pull/20); separate critique
and aggregate acceptance remain pending.

## Exact sources

| Role | Commit |
| --- | --- |
| PR16 parent | `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db` |
| Matched frozen V2 baseline | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| Six-line runtime correction and three regression checks | `f3ceaad98e089aa393c7f5fa650a52695094d979` |
| Final frozen candidate / shared native fixture and driver | `77f204083ab5bea4dc9149d3179daf540a994de4` |
| Earlier fixture, retained first campaign | `997e0b68cd7fa79828dd42c6216dda7cc156fa5a` |

Worktree/branch: `astra/network-input-freshness-v3`, created directly from PR16.
[PR17 coordination](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275040145)
preceded implementation. Evidence/report additions follow the frozen candidate;
the native executions below bind to the exact commits above.

## Source-bound defect and smallest fix

Baseline `game/scripts/network/input_stream.gd:23–41` validates commands, stages
only sequences greater than the consumed acknowledgment, then unconditionally
returns true even when that staged set is empty.

That boolean has a lifecycle effect: `TacticalMatch._input_rpc()` returns on false,
but on true calls `SBPeerLifecycle.active()` and refreshes `_last_peer_input`
(`game/scripts/gameplay/match.gd:997–1011`). Those timestamps control the 30-second
peer idle deadline (`game/scripts/network/peer_lifecycle.gd:49–60`) and 300 ms
action-silence guard (`match.gd:263–273`).

A stock client stops generating commands at 120 pending records
(`game/scripts/network/movement_prediction.gd:29–30`) while continuing to send
the last 12 (`movement_prediction.gd:42–46`, `match.gd:806–815`). During a long
snapshot outage with upstream delivery intact, authority consumes the whole
prefix, yet repeated old batches keep both timers fresh. Released controls cannot
be represented until acknowledgments resume. A modified client can also retain
a slot by repeatedly sending the same acknowledged batch.

The six-line addition at **`input_stream.gd:35–40`** rejects the empty staged set.
Unacknowledged queued duplicates remain acceptable and immutable; mixed stale/fresh
batches still deliver fresh input. There is no additional physics/combat step or
new timeout. This reuses the existing silence guard, including its preservation
of fire/jump/utility edge latches.

The defect is present in the movement/input implementation at `fe6c9c8`, frozen V2
and PR16. It is distinct from already-corrected short-gap synthetic edges, epoch
deadlock, permanent backlog and lost-close transport retention.

## Matched result

Final pair: [baseline-r3](network-input-freshness-v3-evidence/baseline-r3/summary.json)
versus [candidate-r2](network-input-freshness-v3-evidence/candidate-r2/summary.json).
Same Windows host, Python, official Godot binary, external fixture/driver hashes,
commands and conditions; sequential source runs. Both sources and the harness
were clean before/after. Each source completed 16 valid native ENet pairs:
four scenarios × two prediction modes × two repetitions. All 64 peer process
exits/logs are clean. This is headless source-engine evidence.

| Declared measurement | Frozen baseline | Candidate |
| --- | --- | --- |
| Snapshot gap: authority travel in fixed 3.8–4.8 s window, four trials | **1.003–1.020 m** | **0 m** |
| Same window: maximum authority speed | **1.020 m/s** | **0 m/s** |
| Stop after last consumed ACK, before snapshots resume | No stop observed in that interval | **315–332 ms** |
| Stale replay after new input stops at 2 s, four trials | Actor still bound at 34 s | **Retired at 32.057–32.072 s** |
| Retired binding/lifecycle/input/pending-join tables | Still retained | All empty |
| Later fresh leftward command, all twelve eight-second controls | −1.020 m/s | −1.020 m/s |
| Held semi-auto press across interruption, then one real release/press | Two authority shots, ammo 15→13 | Same |
| Owner/enemy private-field violations | 0 | 0 |
| Protocol / diagnostic hit-history frames | 6 / 0 | 6 / 0 |

The baseline fails all eight stale-input improvement gates while passing the
eight steady/short-gap positive controls. Candidate passes all sixteen gates.
[The verifier](network-input-freshness-v3-evidence/verify_evidence.py) recomputes
the decisive measurements directly from the raw authority rows, checks signed
recovery direction, identities, logs and embedded/raw metric equality:
[`verification.json`](network-input-freshness-v3-evidence/verification.json), PASS.
These are builder-run results, not an independent acceptance decision.

### Focused regressions

Both sources pass nine original focused groups: input stream (17 baseline / 20
candidate checks), input lifecycle (3), peer lifecycle (16), reconnect policy (21),
snapshot buffer (15), movement prediction (725; maximum controlled error
0.075834 m), recipient privacy (55), actor authority/presentation lifecycle (183)
and hit history (638). The two additional existing native gates,
`independent_resume_alias_test.gd` and `lost_welcome_test.gd`, also pass on both
exact sources with clean logs. They exercise first-input alias retirement after
resume and interrupted-welcome recovery, call paths affected by input acceptance.
[Supplemental commands/results](network-input-freshness-v3-evidence/resume-gates/summary.json).

### Workload and sensitivity

`game/tests/input_freshness_probe.gd` runs the real Match, actor, movement, combat,
privacy, handshake, ENet and RPC code. An identical collision-only platform above
Relay Yard isolates stale-intent travel from map contacts; bot decisions are
suspended. Input magnitude 0.2 gives 1.020 m/s travel. Server physics poses are the
oracle, rather than predicted client poses.

- **Steady:** eight seconds of ordinary input.
- **Input gap:** omit client processing for 200 ms; a held semi-auto press must
  not become another rising edge.
- **Snapshot gap:** discard application snapshots from second 1 through second 5
  while transport ACKs and upstream RPCs remain live. History must reach 120.
  The gate is under 0.001 m/m/s travel/speed in the stated window, stop within
  350 ms of the last consumed ACK, then signed leftward recovery below −0.9 m/s.
- **Stale replay:** after second 2, a hostile fixture resends its last immutable
  batch and ignores the disconnect. It must retire at 31.5–32.5 s and leave the
  four authority/lifecycle tables empty. This is the existing 30-second idle rule.

Prediction is omitted from configuration in off-mode runs, exercising the actual
default false, and explicitly true in on-mode runs. The final fixture also
publishes an empty start file for 250 ms before the valid shared-start record:
every peer must report a pre-measurement retry without script errors. The driver
bounds Windows rename retries at five seconds while keeping the start in the
future. Candidate recorded 509 intentional reader retries and one publisher
retry; both peers exercised the control in every pair.

## Retained unsuccessful attempts

[ATTEMPTS.md](network-input-freshness-v3-evidence/ATTEMPTS.md) preserves the complete
chronology and original directories. The initial observer lambda had the wrong
signal arity; Windows import metadata marked the preparation worktrees dirty;
one first-campaign baseline client logged a startup JSON/nil-access error; the
empty-barrier control exposed a Windows destination-file rename denial. These
were fixture/preparation failures. The final fixture correction is test-only.

Candidate-r2 completed successfully. Baseline-r2 passed its nine groups, then its
first client crashed before admission with native allocation errors and signal 11
([raw crash log](network-input-freshness-v3-evidence/baseline-r2/1-steady-prediction-off/client.log)).
That failed attempt remains intact. Only the missing unchanged baseline workload
was repeated as baseline-r3, which completed successfully; its controller also
retains [host-memory samples](network-input-freshness-v3-evidence/baseline-r3-host-memory.json).
No startup crash is scored as a gameplay result or relabeled successful.

## Reconciliation with existing PRs and evidence

| PR | Reconciliation against PR16 |
| --- | --- |
| #3 / #4 / #5 / #8 | Stored heads `f60389b` / `0fc8d54` / `e8b9d8e` / `89c0e99` are ancestors. Privacy, interpolation/prediction, bounded admission and validation already exist. |
| #6 / #7 | Latest stored heads `99773c3` / `4401ff8` are not literal ancestors, but `git cherry` identifies their tail runtime patches as already applied. The entire server tree matches PR6; hit history matches PR7. Outbox readiness/quarantine races are already corrected. |
| #10 | Remaining non-ancestor `8100d35` is account-verification evidence documentation. Runtime was integrated through PR11: lost-close timeout/retry and interrupted-resume alias corrections already exist. |
| #11 | `11573e5` is an ancestor; its entire network/server directories match PR16 before this slice. |
| #15 | `228c382` is an ancestor; its entire backend matches PR16. The expected-price guard is integrated; constituent review remains separate. |
| #16 | Game/network/Match/actor bytes are identical between frozen `701ce2c` and report/tooling head `d2439ac`. |

Old unresolved full-capacity reconnect and 64/70 references are historical. V2's
new clean-source 74/74 matrix and 12/12 ten-client campaign remain attributed to
V2, not this candidate. Its retained blackout drops both directions for two
seconds; this slice tests four-second selective application snapshot omission and
acknowledged-only replay. Existing input tests covered a redundant packet with
one new command, and full-history recovery across an epoch change
(`input_lifecycle_test.gd:58–76`), not stale-only acceptance renewing both clocks.

## Contracts and remaining engineering

[Source preservation](network-input-freshness-v3-evidence/source-preservation-r2.json)
records protected Git-blob hashes, directory equality and all 13 RPC pairs. The
only changed runtime file is `game/scripts/network/input_stream.gd`. Protocol 6,
default-off prediction, disabled live rewind, recipient privacy, actor authority,
ranked-disconnect and marketplace semantics retain their contracts. Match, actor,
Gemini AI, Claude assets/presentation, backend/server and Sol's campaign/matrix
scripts retain their bytes.

**Biggest gap: history saturation still prevents fresh client intent.** This fix
makes authority stop under the existing silence policy; a client whose 120 pending
commands cannot be acknowledged still cannot send a new release/turn. It does not
provide resynchronization or improve prediction collision accuracy. The next
bounded experiment is fresh-intent recovery under long asymmetric outages while
preserving sequence windows and action edges.

Other concrete engineering remains beyond docs/research:

- Opt-in prediction/collision accuracy: V2 retained 0.519 m p95 ACK divergence at
  100 ms and 0.609 m under blackout. The separate V3 prediction worker owns this
  investigation. Prediction-disabled ACK differences are stale authority poses,
  not prediction error.
- Brief action delivery when backlog above six discards all but two commands
  (`input_stream.gd:73–79`); no extra combat steps may compensate for lost intent.
- Possession-generation invalidation before any live rewind experiment;
  `hit_history.gd:30–35` recognizes death/team/teleport, not stationary ownership
  replacement. Diagnostic recording and live damage rewind stay disabled.
- Initial account admission interrupted after ticket consumption but before its
  first welcome still needs a fresh ticket (documented reconnect limit).
- Active parallel implementation lanes: durable receipts in PR18, trade-read
  batching in PR19 and Sol's portability/provenance work in PR17.
- B-28 remains partly implementation work: `/market` has SQL filters and a
  500-row cap (`backend/app.py:246–258`), but no paging cursor/offset; `Trade` has
  no expiry timestamp (`backend/models.py:71–79`). B-27's price guard is already
  implemented in PR15/16; B-21 is the separate receipt-recovery slice.

The isolated headless workload does not establish rendered/device performance,
human feel, public Internet security, sustained load, a complete V3 matrix,
exports or release quality. Keep this draft for the separate critic and aggregate
integration gates.

## Reproduce and inspect

Official Godot `4.7.2.stable.official.ed1daf0bf` Windows executable SHA256:
`ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`.
Final driver SHA256: `5c84f2a8cdd58832f2087cebaafbe183a39808cfbc3fb2cfb2cb8dfe7c556317`.
Final probe SHA256: `ec6ed6a056d8a50c1b6554d0a741742802ec42fb26c056711be5790e2dbf9f97`.
These identify measured working-tree bytes; checkout line-ending normalization
can affect file hashes. Native source identity is also bound to the Git commit.

Create owned detached worktrees at `701ce2c` and `77f2040`. Prepare each once with
`godot --headless --path <tree>/game --editor --import`, using Python
`subprocess.run` with captured output and an actual wait. Check exit/logs; a direct
PowerShell GUI launch is not an engine-exit receipt. Review generated metadata,
restore only tracked `game/assets/**/*.import` in these fresh worktrees, retain
the ignored `.godot` resource/class caches, and confirm both Git statuses empty.

Run sequentially, with output outside both source trees:

```text
python <candidate>/scripts/test_input_freshness.py --godot <godot4.7.2> --source <baseline> --out <evidence>/baseline-r3 --skip-import --checks --repeats 2 --barrier-control
python <candidate>/scripts/test_input_freshness.py --godot <godot4.7.2> --source <candidate> --out <evidence>/candidate-r2 --skip-import --checks --repeats 2 --barrier-control --expect-fixed
python <published-evidence>/test_resume_preservation.py --godot <godot4.7.2> --baseline <baseline> --candidate <candidate> --out <evidence>/resume-gates
python <published-evidence>/verify_evidence.py <evidence>
```

Both sources must remain frozen until commands exit. Baseline's failed improvement
gates are intentional observed defects; process/log/source validation still must
pass. `--expect-fixed` makes improvement failures fatal for the candidate.
The [evidence index](network-input-freshness-v3-evidence/README.md) links all raw
timelines, logs, commands, source identities, unsuccessful attempts and checksums.
