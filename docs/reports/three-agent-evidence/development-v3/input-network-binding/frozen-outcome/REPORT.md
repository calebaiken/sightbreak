# Independent blinded neutral-input outcome verdict

## Outcome and scope

**sample-H is the observed safety-outcome winner over sample-T. This is not release approval, authenticated native execution, or a general network-performance claim.** Both sample identities remain unknown. The complete safety bar is not established by this packet: the measured stale-input improvements are strong within the recorded fixture, while human/device, real-network, comprehensive protocol/authority/privacy and longer-session coverage remain open.

I read only the two explicitly permitted Git blobs from commit `0cbc3ae7a9a017aa179eaeff61cf902629de1c0d`, exporting bytes with Python `subprocess` and `git show` into a new isolated directory. No branch/parent files, identity map, source identities, neighboring files, or implementation/fixture-source contents were inspected. No packet-supplied code was executed. The only execution was small serial offline analysis under the exact approved CPython 3.13.15 executable; no native engine, database, network or services were used, and the repository/index were not edited.

The supplied external pins match:

- ZIP: `8fb111324051b4bfc590a216ab09c107ef0c10605f755b7e481757d125172112`
- Manifest: `fe83c4bdcc1ea662f034ff4ebc340a4e115ed27e8a7d404a2aa80175d84146ce`

All **362 listed payloads** match their byte lengths and SHA256 values. The ZIP has exactly **363 regular members**: those payloads plus the byte-identical manifest, totaling 15,749,223 uncompressed bytes. Inventory checks reject traversal/absolute/Windows-unsafe names, case collisions, duplicates, symlinks/nonregular entries and encryption. ZIP CRC reads and extracted-byte comparisons pass. No omitted or extra member was found.

I independently processed **all 55,743 actual peer rows**, all 64 peer native logs, 32 capture receipts/barriers/ready records, and all 22 focused gate logs/receipts. The per-sample row totals are 27,874 and 27,869. Full row values and independently computed deltas/ages are preserved in `raw-audit.jsonl`, not merely selected excerpts. Reconstructed motion windows, every ACK/control/liveness/snapshot change reference, silence/retirement/recovery structures and capture summary calculations agree across all 32 cases (absolute numerical tolerance 1e-10). This is internal consistency, not independent truth/authentication of the historical recorder.

## Primary matched outcomes

Each scenario has prediction off/on and two repeats: four cases per sample. Travel uses inclusive authority callbacks at 3.8-4.8 s, not an invented exact one-second wire interval. Both endpoint displacement and cumulative absolute x movement were recomputed; speed and move controls were inspected throughout, preventing a zero-net-displacement false pass.

| Observed test | sample-H | sample-T |
| --- | --- | --- |
| Snapshot-gap stale travel, four cases | 0 m, 0 m/s | 1.003009-1.020009 m at about 1.02 m/s |
| Replay stale travel, four cases | 0 m, 0 m/s | 1.003009-1.020010 m at about 1.02 m/s |
| Actual silence control-clear opportunities | 8/8 clear at about 0.316667 simulation s of accepted-input age | 0/8 clear before t=5; stale controls persist |
| ACK-anchor to sampled x-axis rest, actual stale cases | 315-336 ms, 8/8 below the separately declared 350 ms gate | No rest before t=5, 0/8 |
| Fully-ACKed observed fixed-sequence replay extends activity | No, 0 subsequent liveness updates after final ACK in all four | Yes, 941-959 subsequent liveness updates despite fixed final ACK |
| Replay binding retirement and four cleanup counts zero | 4/4, observed t=32.057-32.072 s | 0/4; still bound and moving through about 34 s, counts 1/1/1/0 |
| Steady/short-input-gap travel controls | 8/8 stationary in requested travel window | 8/8 stationary in requested travel window |
| Standard-case later authority direction and fire/ammo | 12/12 leftward vx about -1.02; 2 shots, ammo 13 | Same 12/12 |

The eight steady/short-input-gap travel passes are controls, **not eight additional demonstrations of silence neutralization**. The input callback omission is only 200 ms and does not by itself exercise the >0.3 s silence threshold.

### Exact per-case stale timing

All times below are sampled relative wall seconds except the stated simulation age. Prediction describes the client mode. H's observed clear age is about 0.316667 simulation s in every row; the preceding moving row is about 0.300000 s. T has no corresponding clear/rest before 5 s.

| Case | Scenario | Prediction | H final pre-resume ACK t | H first move_x=0 t | H ACK-to-rest ms | H replay retirement t |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| case-05 | snapshot-gap | off | 2.949 | 3.249 | 332 | n/a |
| case-06 | snapshot-gap | on | 2.945 | 3.227 | 315 | n/a |
| case-13 | snapshot-gap | off | 2.964 | 3.264 | 331 | n/a |
| case-14 | snapshot-gap | on | 2.960 | 3.243 | 316 | n/a |
| case-07 | stale-replay | off | 2.057 | 2.357 | 335 | 32.060 |
| case-08 | stale-replay | on | 2.067 | 2.367 | 333 | 32.072 |
| case-15 | stale-replay | off | 2.077 | 2.360 | 318 | 32.061 |
| case-16 | stale-replay | on | 2.056 | 2.356 | 336 | 32.057 |

For an auditable example, H/case-05 server rows 193-196 have control/speed pairs `(+0.2,1.02)`, `(0,0.553333)`, `(0,0.086667)`, `(0,0)`. Thus control neutralization is not an instantaneous physical stop. Rest follows the first cleared row by about 0.033333 simulation s; the entire ACK-to-rest delay is not the simulation silence deadline. The last-input age is computed from **simulation_t minus last_input**, not from the ACK wall timestamp. Serialized floating-point values around 0.300000 can differ by roughly 1e-15; they do not justify sub-frame boundary claims.

### Replay/lifecycle interpretation

In every replay case, the authority ACK reaches the observed client's maximum generated sequence (H 174/175/175/174; T 175/164/173/174 in case order 07/08/15/16), then remains fixed. The raw client sequence remains fixed too. H's accepted-input simulation timestamp and wall lifecycle timestamp stop renewing; rejected counters continue increasing and binding is eventually removed. T repeatedly refreshes both timestamps while ACK and command sequence remain fixed, keeps move_x about +0.2 and vx about +1.02, and remains bound. After the ACK anchor, H accumulates only about 0.283-0.300 m of x travel before rest, versus T's 32.589-32.606 m through the retained end.

H/case-07, for example, last changes liveness at row 123/t=2.057, remains bound at row 1921/t=32.039, and is unbound at row 1922/t=32.060. The independently recomputed inactivity sampling brackets across the four H replays span **29.982-30.023 s**, consistent with a 30 s expiry. They do **not** prove an exact 30,000 ms boundary: server `start_msec` was not retained, so subtracting `t*1000` from absolute `peer_last_input_msec` would be invalid. Binding retirement is not a claim that the actor was destroyed; only the four reported peer/lifecycle/queue/pending-join tables are shown empty.

The fixed batch's bytes were not captured. “Fully ACKed replay” is supported by the observed max-sequence/ACK plateau and configured replay, not by an independent payload/parser audit. H's rejection counts are **900 per replay**; T reports zero. These counters are not silently dropped or equated with fresh-input failure.

## Preservation and counter-controls

### Legitimate queued/unACKed tail and ACK recovery

All eight snapshot-gap cases reach the 120-command history cap. H first reaches it at 2.884-2.902 s; T at 2.881-2.947 s. Production remains frozen until snapshots/ACK handling resumes around 5 s: this unresolved loss of fresh intent must remain in any improvement claim.

At the sampled H cap callbacks, authority still trails the frozen cap sequence by 3-5 commands. It subsequently reaches sequence 228 in all four cases with **zero recorded rejections through that ACK**, then rejects later redundant traffic. This supports preservation of the real queued/unACKed tail rather than indiscriminate duplicate dropping. It does not prove exhaustive loss/reordering retry correctness without packet data.

H resumes accepted snapshots at 5.018-5.043 s, pending drops from 120 to 1, sequence advances to 229, and authority ACK resumes at 5.049-5.075 s. T also recovers (snapshots at 5.032-5.063 s; ACKs at 5.050-5.109 s). Both remain peer-bound throughout these eight-second observations and later apply actual signed leftward authority movement. Every standard case's 7.0-7.8 s authority window has largest vx about -1.02 m/s, not just an unsigned “recovered speed” boolean. Only about 2.95-2.98 s of post-snapshot-recovery client observation exists, **not a later thirty-second healthy-session soak**.

Rejection counter controls are important: H's four snapshot cases report **62,63,62,63**, its four replay cases **900 each**, and its eight healthy controls **0**. T reports **0 in all sixteen cases**. In H the snapshot rejections begin after the authority reaches the cap sequence; recovery still succeeds. Rejection totals cannot be turned into exact UDP replay packet counts because callbacks can aggregate events.

### Action edges and authority

All twelve standard cases per sample finish with two shots and ammo 15 to 13. Every authority row satisfies `ammo + shots == 15`; shot increments align with fire-held rising transitions, and genuine release followed by press yields the second shot. H's stale-control clear keeps fire_held true through silence; no silence-induced second shot appears. Replay has one shot/ammo 14; the configured client replay does not process the later release/press schedule, so that missing second shot is **not** an edge regression. On H's eventual retirement, the latch can clear as part of retirement, not as a false silent release while bound.

The focused lifecycle log for both samples records `steady_held_shots=1 gap_held_shots=1 gap_rejected=0` and the epoch counter control `accepted=200 ack=200 client_sequence=200 pending=0 first_sequence=200 last_sequence=200`, with 3 checks and 0 failures. Additional jump/utility latch outcomes are not individually exposed by the raw live captures or these summary lines; no comprehensive edge-preservation proof is claimed.

All server ACK traces are nondecreasing. X displacement is internally consistent with per-step server vx integration to maximum residual below 1.8e-6 m across all cases. This supports authoritative x-motion consistency, not authentication of the server or full movement/collision correctness.

### Protocol/privacy/default prediction/live rewind

All 64 peer reports record protocol **6**, zero privacy violations and zero active hit-history frames. For all sixteen prediction-off client cases the launch receipt omits `--prediction` and the raw client report is false; the on cases explicitly request and report true. These modes must not be traded away for the stale-input improvement. The privacy counter and focused 55-check privacy test are corroborating historical observations, not packet-by-packet privacy re-audit: no raw snapshot payloads were retained. Zero active history frames is the measured live-rewind control, not authorization to enable rewind. No implementation or shipped-default source was reviewed in this blinded phase.

### Focused gates and failures retained

There are 11 focused gate process receipts per sample, all with recorded exit 0, matching log hashes and no unexpected native-error scan hits. Numerical checks logged per sample are 1,699 for H and 1,696 for T, plus the structured lost-welcome record. Input-stream checks differ **20 versus 17**; shared logged counts are lifecycle 3, peer lifecycle 16, reconnect 21, snapshot buffer 15, movement prediction 725 (maximum_error_m=0.075834), privacy 55, actor lifecycle 183, hit history 638 and resume alias 23. Counts are not equal assertion coverage or proof that each hidden assertion is sound.

The alias logs retain all 23 PASS lines, including lost-welcome recovery, bounded previous-credential lifetime, no eviction of an unconfirmed live owner, and old-alias invalidation on first accepted input. Two terminal `PROTOCOL_CLIENT_FAILED` lines are expected credential-denial controls, not discarded errors. The separate lost-welcome JSON records the same actor restored, old client credential retained, old credential no longer valid, connected final state and valid suppression fixture; its stated scope is one native process with ENet/application delivery suppression.

The completed comparison's peer native logs have completion markers and no unexpected error lines. That is **not an all-attempts clean-run claim**. All seven failure-retention indices are preserved verbatim, including dirty preflights, an earlier startup JSON/nil-access error, and an allocation crash before first admission. The detailed original failure artifacts are not in this neutral packet and were not inspected. They remain unresolved selection/robustness limitations, not erased trials.

## Limitations and remaining gates

- This is historical, unsigned recorder output. External hashes establish byte identity; controller exit 0, readiness strings, native banners and clean-source receipts do not authenticate actual execution. No new native run was authorized or performed.
- Only two repeats per deterministic scenario/mode on loopback, no randomized impairment seed and no true wire-loss/reorder/ENet trace. Fixed sample/run order and variable warmup prevent general latency, CPU, startup or total-runtime speed comparisons.
- Source role spawn/ready/latch timestamps and exact wall-clock origin are missing. Repeated millisecond wall timestamps occur in replay/on client traces (one row in H, eight in T); maximum callback gaps reach 75 ms server/64 ms client in H and 109/137 ms in T. Physics steps remain about 1/60 simulation s. Nominal rates are not actual datagram timestamps.
- Replay counters show accepted snapshots continuing while client sequence and pending remain frozen. This is not a normal client fully maintaining ACK history, a post-replay fresh recovery test, or mixed redundant-plus-continuing-fresh-input traffic. Higher valid sequences also do not prove human presence.
- No grounded flag, y/z position/velocity, real device/rendered behavior, full-vector stop or individually logged jump/utility edge outcomes. Privacy payloads and exact replay bytes are absent.
- Source identities, implementation invariants, source cleanliness and actual process custody cannot be resolved in this blinded phase. Shared source/provenance contents were deliberately not inspected. None of these gaps are filled by equal-looking log hashes or summary booleans.

**All original human/device acceptance gates remain. Protocol must remain 6; prediction must remain default off; live rewind must remain off; authority/privacy/retry/edge safeguards must remain.** The only supported comparative conclusion is sample-H's substantially better measured stale-input safety with the listed observed preservation controls. Broader release approval is withheld.

## Frozen record

`sample-H-assessment.json` and `sample-T-assessment.json` contain individual case criteria, exact row references, all control/gate counters and neutral verdicts. `comparison.json` retains every failure/not-applicable status and the coverage gaps. `raw-audit.jsonl` contains every actual peer row and focused log plus independently recomputed deltas. `crosschecks.json`, `audit-validation.json`, `inventory.json`, input pins, failure index, original neutral ZIP/manifest and executed analysis scripts provide the audit trail. `SHA256SUMS.txt` covers these payloads; `FROZEN.json` binds that ledger and the explicit UTC freeze record. Its separate checksum is the external freeze handle, not a cryptographic signature or trusted timestamp attestation.
