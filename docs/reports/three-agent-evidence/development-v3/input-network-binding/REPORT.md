# Network input freshness — post-freeze source binding

## Source-qualified recommendation

**Recommend accepting the narrow fully-ACKed-replay freshness guard for integration consideration, preserving existing safeguards and subject to main's integration decision and a new combined-source CI pass.** This is not release acceptance, a broad PR20 integration pass, or a new full-network victory. No engine/campaign/CI rerun was performed. Historical native measurements must not be represented as that future CI pass.

The old blinded outcome remains unchanged. This separate report binds the recorded outcomes to released identities and committed sources after the freeze; it does not rewrite the earlier network verdict or the separate published component packet.

| Frozen sample | Verified released executed source | Source qualification |
| --- | --- | --- |
| H / candidate-r2 | `77f204083ab5bea4dc9149d3179daf540a994de4` | Production scripts exactly match runtime `f3ceaad98e089aa393c7f5fa650a52695094d979` |
| T / baseline-r3 | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | Frozen V2 source; no new integration claim |

## Release, original references and old freeze

The exact mapping at release commit `a78a0dc927fc32de33614ff5339e15750b04aa2b`, `docs/reports/network-input-review-release/mapping.json`, is **212,748 bytes**, SHA256 `1d5b1cbed67c7fb94c2afe72c64b52b44c1b0915720cd0ddbc21151833709709`. The released sha/verification files agree. I independently checked all316 original counterpart Git blobs and11 source commitments rather than accepting coordinator review prose as proof. Linked GitHub comments were not fetched or used as independent execution evidence.

The release publishes a key and reference checks. The first probed original-data path is absent at a78. Its mapping resolves the original artifacts at exact evidence commit **`1627a9a0ca2a954fe8f246c42ff2f205c578b5c5`**. All316 were independently resolved there, with declared length/SHA256 and computed Git blob identity verified. They are not mislabeled as original-data blobs physically present at the a78 path. The release object was already local, so no fetch/network access was needed.

Before reading the key I verified the untouched old network freeze and all17 ledger payloads (28,179,135 bytes):

- FROZEN SHA256 `e944002cdd8980f5e3f75d24efdc62b1041458b1a2a52138672a2e9a5c6671a0`;
- report `9ed4a4e61f16612067978db54ad584a201315e0935328b5b39f2746231124bdc`;
- ledger `ae0aee6f6e5019f18490ab5162501bcc7a85fd9ddbce5c552444d9183872031d`.

The exact neutral ZIP remains `8fb111324051b4bfc590a216ab09c107ef0c10605f755b7e481757d125172112`, and manifest `fe83c4bdcc1ea662f034ff4ebc340a4e115ed27e8a7d404a2aa80175d84146ce`. All362 payloads and363 safe ZIP entries including the identical embedded manifest verify. No old evidence content or attributes were changed. Local hashes/chronology bind bytes, not trusted time, signed native/OS execution or historical authorship.

## Complete neutral-to-original bridge

| Neutral category | Count | Verification |
| --- | ---: | --- |
| Raw JSON, peer/gate logs, barrier/ready records | 278 | Exact original mapped Git bytes |
| Capture receipts | 32 | Exact JSON reserialization and documented command redaction; captured metrics unchanged |
| Derived timeline indexes | 32 | Bound to exact source rows and the immutable old independent all-field recomputation |
| Run manifest | 1 | Cases, environment, source continuity, two controller receipts and22 focused gate receipts linked to originals |
| Canonical source copies | 7 | Exact committed bytes |
| Source excerpts | 4 | Exact declared line ranges/range headers reproduced |
| Administrative/descriptive/verifier artifacts | 8 | Pinned exact bytes; no claim they are native output |

Only the named author policy flags (`transport_authority_privacy_pass`, `recovery_and_edges_pass`, `improvement_gate`) and original absolute command paths are removed/replaced in the32 capture receipts. All shared numeric metrics and process return codes remain. Roles, ports, scenario, durations and prediction flags are preserved. No native rerun is used to reconstruct these identities. O0316 is the retained author `ATTEMPTS.md`, not an extra trial or independent witness.

The original summaries identify executed commits/game trees, source-before/after clean strings and InputStream working-file hashes. Their recorded game trees resolve in Git and their before/after fields match. The shared external probe/controller digests and all22 gate exit/duration/log-hash receipts match the neutral manifest. These remain **unsigned author/controller records**, not proof that every declared byte/cache was actually loaded.

## Exact source representations, not unexplained normalization

The11 source artifacts resolve to their recorded Git objects. Probe/controller disk digests match Git directly; **nine additional source-snapshot digests** are exactly reproduced by replacing each canonical LF byte with CRLF and changing nothing else. The per-run InputStream digest is a separate commitment and must not be conflated with those nine.

H's run hash initially matched neither canonical LF nor uniform CRLF. It has now been exactly reconciled:

| InputStream representation | Bytes | SHA256 |
| --- | ---: | --- |
| H committed LF | 3,463 | `b455205d827134830637f03457cc67e4e321721d91a7d840941fc74e1b26c88e` |
| H uniform CRLF, not the measured hash | 3,556 | `ebd0f6c250554e94364ae4de02b6fc88451db0a3e401f45c36c7fa4077a5f7aa` |
| H exact measured-hash reconstruction | **3,547** | **`6d344ac7892ed4f3d22003a2ca8e0a2d0813bceaa804aeff1c8d2ca7c2559c61`** |
| T committed LF | 3,177 | `60d92e1cacc838867f9241379cbf3bc8b27a025fd1b91ca191effc37354d7ccc` |
| T uniform CRLF measured-hash reconstruction | **3,264** | **`25e60f86e3d9d05b5e84a7f258f2775e98fbe1814a429176f417dd9db3bda19d`** |

H's exact recipe is **LF on canonical lines33-41 inclusive, CRLF on every other line**. A bounded offline check found the matching digest after2,489 candidates. Both reconstructed files are published, explicitly labeled reconstructed. Replacing CRLF with LF in them recovers the canonical committed bytes exactly; no non-newline byte changes. H records the same digest before/after the historical run. Preliminary mismatch diagnostics remain preserved and are explicitly superseded by the exact reconciliation.

No checked source-byte discrepancy remains unexplained. That does not make a newly reconstructed file an original retained disk capture, nor authenticate imported cache/process execution. Nine exporter source snapshots, the measured InputStream hashes, and native loaded-byte attestation are distinct evidence categories.

H's executed and runtime `game/scripts` tree is identically **`329f7816683e3c885521f50a99d6106e30bd1ba4`**. Their complete game-tree diff contains only the freshness probe and its UID sidecar. This supports qualification to f3ceaad production scripts, not a claim about the current/future combined branch or its CI.

## Actual source mechanism and caller/timer gates

InputStream at77f2040/f3ceaad validates commands, stages sequences above authority ACK, and rejects empty staged work. Fully ACKed replay therefore returns false/increments rejected. A queued but unACKed duplicate remains staged/nonempty and accepted, without rewriting its first queued payload. Mixed genuinely newer intent remains valid. The older701ce2c implementation lacks the empty-staging guard and returns true after an empty insertion loop.

Static committed source supplies the caller link:

- Match997-998 returns on accept=false, before lifecycle.active at999, alias confirmation, **conditional** `_last_activity` at1009-1010 and `_last_peer_input[id] = _elapsed` at1011. True does not make the conditional activity predicate unconditional.
- PeerLifecycle.allow_input39-47 gates admission/expiry/rate but does not renew last_input. Active49-51 renews an eligible live peer. Idle expiry is **>=30,000 monotonic wall milliseconds**; Match821-825 enforces disconnect and invokes cleanup.
- Match advances `_elapsed` by physics delta. Authority259-272 neutralizes after **strictly >0.3 simulation seconds**, ticks authority and restores held edge latches. Control clearing is not instantaneous physical rest or a300ms wall guarantee.
- Movement prediction stops producing sequences when pending.size>=120. The bounded history can still be resent. The guard prevents consumed replay renewing activity; it does **not** unfreeze fresh intent before ACK processing resumes.

This source reasoning is consistent with the frozen historical native rows/logs. It is not a new execution of merged/current source, a whole-program proof about every activity path, or a fresh attestation/security test. Full exact source and caller/clock excerpts/proof records are in the evidence archive.

## Historical observations and limits remain

The unchanged blinded assessment processed55,743 rows,32 pairs,64 peer logs and22 focused gates. H cleared all8 actual stale opportunities around0.316667 simulation seconds of accepted-input age, reached sampled x-rest315-336ms after the ACK anchor, and showed0m/0m/s stale windows versus T's about1.003-1.020m at1.02m/s. H retired all4 replay bindings at32.057-32.072s with four reported counts empty; T remained bound/moving through34s. These are historical observations, not new benchmark runs. Healthy controls, queued-tail/ACK recovery, signed later leftward movement, fire/ammo outcomes and adverse/rejection counters remain preserved.

The baseline controller can exit0 while improvement gates fail because `--expect-fixed` is false; H uses that flag. Root/controller exit0 is not proof of equal behavior or every safety criterion passing. Awaited child returns, native markers and reports are corroboration inside unsigned author-run evidence, not authenticated OS execution.

Retained boundaries:

- Simulation and wall clocks differ. The exact server relative wall origin is absent; expiry is callback-bracketed around30s. ACK-to-rest is not the300ms simulation deadline.
- Snapshot impairment is deterministic application omission on loopback, not seeded WAN/UDP loss. Identical fixture settings do not prove identical delivered datagrams. No PCAP, retransmission schedule, snapshot payload archive or fixed replay batch bytes were retained.
- Replay client_tick returns before normal maintenance at t>=2 after resending its last stored compressed batch. Pending/sequence freeze while snapshot counters can continue. This is not a stock-client long-blackout recovery or continuing-fresh-intent test.
- All snapshot-gap cases hit the120-command cap, freezing fresh intent until ACK processing resumes. They end at8s: about3s post-recovery, not another30s healthy-session soak. Higher valid sequences do not authenticate a human.
- X/vx/move/fire/shot/ammo rows do not prove full3D contact/stop, rendered feel, device behavior or every utility edge. Focused fixture gates keep their own controlled scopes.
- Privacy counter0 and focused privacy assertions are not missing-wire-payload re-audit. Protocol6, prediction default-off and zero live history/rewind settings remain required.
- `--skip-import` uses unarchived imported caches. Source-tree/digest/clean-status agreement is not loaded-byte or OS process custody. Historical execution is not today's combined-source CI.

### Four structures empty is not complete actor cleanup

Reported counts cover `_peer_actors`, `_peer_lifecycle.peers`, `_input_stream.queues` and `_pending_joins`. Source cleanup forgets stream-owned state and removes binding while retaining the actor for takeover/reservation handling. Actor-level ACK storage, simulation-input timestamps, `_elapsed` and actor state are **not claimed erased**; raw ACK/timestamps persist after peer_count0. Do not turn the four-count observation into complete actor/ACK/activity/simulation clearing.

## Attempts, accountability and acceptance

The316 exact originals include author chronology and controller receipts. Seven failure inventory hashes reproduce exactly using pretty JSON plus final newline, accounting for369 prior files. Those369 old content blobs were not reread or republished, but their precise Git paths/hashes/sizes are retained in the released mapping. Earlier preparation, fixture, startup and allocation failures remain failed/superseded, not relabeled clean trials. The original receipt includes baseline-r2 exit1; candidate-r2 is retained and baseline-r3 supplies the completed baseline. There is no all-attempts success-rate claim.

The historical controller source explains Popen/wait/log/barrier/report construction; a program cannot independently attest its own past execution. Release prose, reviewer links and matching hashes do not supply trusted timestamps or signed capture. This review's failed schema/path/newline assumptions are preserved alongside their exact resolutions; no producer/native rerun occurred. Final findings supersede explicitly preliminary diagnostics, never the earlier frozen verdict.

**Accept only the narrow source-qualified evidence/change for integration consideration.** Main owns integration and new combined-source CI. Human/device, protocol6/default-off prediction/rewind-off, privacy/authority/edge preservation, stock-client long-blackout and broader integration gates remain. This is not release approval or that future CI pass.

## Publication and omissions

The exact neutral ZIP/manifest and released key files are included. `binding-evidence.zip` losslessly includes all316 original counterparts,11 source artifacts,18 production/config objects, exact transformation proofs, reviewer receipts/scripts and compact unchanged old freeze core. Every member is verified against its complete outside inventory after compression. Reconstructed working files are separate and labeled.

The old large reviewer raw-audit JSONL,369 prior failed/superseded contents, engine executable, unarchived caches and documentary GitHub links are omitted/referenced precisely in `omissions.json`. All raw native data within the362-payload neutral ZIP remain included. The compact old freeze view is not falsely presented as a replacement complete original directory.

Local attributes disable text conversion/filter/ident/working-tree encoding and are Git-checked. Every published payload, archive member and the complete file set is verified before handoff. Repository writes stay exclusively in the new `input-network-binding` subtree. No checkout/branch/stage/commit/push, posts, engine/services/DB or new network campaign occur. Final hashes bind local bytes, not signed execution or trusted time.
