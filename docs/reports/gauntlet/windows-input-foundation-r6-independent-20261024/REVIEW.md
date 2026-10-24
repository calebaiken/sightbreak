# Exact R6 interval component — REVISE

Reader source6ef4d145ab70ed943c54ec26865e0c884b64b1a9, SHA256fab0711b9f239654a31cac745d4778eed8691d617eccea39c7fccabc6593fdf0; original clean builder handoffb5a3ea334e5a2b02fe6600683823c4f21e56b23e. Additional immutable builder query82d05d8aa4f9a1d93f2c84cc34ddf271b53cfcba does not change that source or its original182-member evidence. R6 fixes all three exact R5 necessities but misses two more source-proved owner bounds. Both initialized source views reproduce the misses. Current source is REVISE, with no whole-reader/native/replay approval.

Prospective f84cd7bd was registered before R6 inspection. Concrete models/source activation63112ce3 and setup correction were frozen before execution; additional query assessmentf87784ab was registered before independent replay. This is the same reused critic thread. I built earlier R7 expiry code/model/tests and cannot independently approve inherited R7. I did not implement Root's R3/R4/R6 source or the different R5 builder's source. This review judges new R6 necessities and composition. The separate Linux protocol reservation was cancelled and was not activated.

## Supported owner-bound findings

The query author is the R6 builder, not a critic. I independently derived the expected statuses from InputStream operations, verified the exact mutations, and reconstructed the positive lifecycle/stream/counter/latest/control projections using my separate Complete/Forward model rather than Root's CompleteAuthority. Every compared projection key and actor.input agrees. Schema checks pass for every row. Frame/resource/client fields remain synthetic; this is a bounded source proof, not native provenance.

| Immutable query | Necessary fact | Expected / actual in both views |
| --- | --- | --- |
| sole-other-pop/positive | selected ACK9 stays2 while the sole new global pop belongs to10 | UNKNOWN / UNKNOWN |
| sole-other-pop/contradiction | change only finalACK9 from2 to3 | INVALID / UNKNOWN |
| same-pop-replayed-ack/positive | a new local pop advances ACK2→3 and latest consumed sequence3 | UNKNOWN / UNKNOWN |
| same-pop-replayed-ack/contradiction | change finalACK and latest consumed sequence together3→2 | INVALID / UNKNOWN |

Both witnesses complete Match's required pops after each added authority-tick observation, including both bound peers at13000. The later18000callback pops only the named stream;19500observes the next empty-pop tick. Each compared selected-stream interval is still bound peer9/generation1/epoch1, with exactly one new global consumed call. No disconnect, epoch reset or stream replacement explains either mutation.

Source InputStream.accept14–48 stages only commands above that stream's current ACK; pop69–85 removes its oldest queued key and writes that sequence. Another stream's pop and acceptance cannot write this stream's ACK. Consequently, if the newly latest global pop names a different identity, at least one of the counted pops is not local. When global C=1, local Cmax=0: selected ACK cannot change and no selected backlog skipping is possible. If the newly latest pop is local, local Cmin>=1 and its ACK must strictly advance. Equality to a corrupted latest sequence does not prove that advance. These are necessities from observed ownership, not an invented allocation of anonymous calls.

StreamObservationIntervals currently uses global consumed==0 for unchanged ACK and otherwise checks equality only when the latest owner matches. Thus a sole other-owner pop permits an unjustified selected ACK advance, and coordinated latest/ACK corruption can preserve equality without a real new pop. The old deferred queue model stops at the earlier UNKNOWN and cannot provide the missing later checks.

The supported general bounds are local C in[1,C] if newly latest owner is this identity, or[0,C-1] if it differs. Local skipping requires a local pop. These bounds can constrain ACK and conservative queue intervals without reconstructing exact receipt allocation/order. Legal sparse sequence gaps must still permit large ACK jumps; no count-derived upper jump is supported. Preserve the original UNKNOWN controls and the stopped partial inference rather than forcing them CONSISTENT or resuming unsound state.

Exact builder query source, all four full input/result arrays, manifest, original guard/output and10verified members are under frozen-additional-query. Independent exact replays and reconstruction proofs are under candidate-additional-query and depth-additional-query; each is2/4matches, two supported negative misses, exceptionnull and zero forbidden-effect attempts. No additional arbitrary query cases were generated after this frozen assessment. Reproduce with fresh output paths:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<source>/scripts:<sealed-R5-controls> taskset -c 4 python3 <this-report>/controls/pure_runner.py --guard-result <absent-guard.json> <this-report>/controls/assess_frozen_query.py --source <exact-6ef-source> --output <absent-output>
```

## Other actual checks, with scope retained

| Check in each source view | Actual result |
| --- | --- |
| Independent stream/component and callback expectations |247/247matches:156isolated component,86complete projection,5mutation baselines |
| Targeted new interval/integration mutations |5/5meaningful changes detected |
| Sealed completed R5 necessity control |5/5; prior R5 was2/5; positive staysUNKNOWN |
| Exact retained R4 corpus |49/49 |
| Frozen isolated R5 projection model |3060/3060, preserving its limited projection scope |
| Additional owner query |2/4, as above |
| Literal unchanged whole suite |158methods,45failure events,1error,0skips; NOTPASS |

The independent component cases use source-built key sets with ACK absent/10 and queue cardinalities0/1/6/7/12/120, legal batches, queued duplicates, own/other-owner pops, backlog reduction, epoch reset and generation changes. These are isolated stream necessities, not complete Match histories. The independent composition cases complete every added tick's ordered pop loop, test legal sequence gaps2/3/61/121, two clock phases, selected-peer switches, pending RX, immutable queued duplicates, bound epoch reset and disconnect/replacement/new generation. Other envelope fields remain synthetic. Finite one-way positive witnesses do not prove complete history closure or all unobserved allocations; satisfying the tested bounds does not establish whole diagnostic completeness.

The five in-memory mutants remove integration, ACK monotonicity, zero-C equality, newly latest owned-pop equality and queue cardinality checking. Each has a nonredundant registered control and changes expected INVALID to UNKNOWN. No candidate file was changed. Nine new builder methods pass in a separate own-view run and within both literal runs; no failure belongs to the new file.

Both literal captures contain3,180actual calls and raw JSONL SHA256d9ce65f7afe9d24bc57c1deab27353765621c40cd655024b31b3d7a444f11548. All46failure identities match sealed R5 exactly. No remaining failure is silently classified as a fixture issue or counted passing. The separately supported23-leaf constructor amendment is UNAPPLIED and its original failure remains; no normalizer/helper/assertion change was made or authorized by this review.

All guarded pure runs record zero forbidden process/API/proc attempts, including intentionally nonzero literal and owner-query runs. Two initial review setup failures remain: models.py had a missing closing print parenthesis and failed before candidate import; a copied control lacked its immutable dependency on invocation PYTHONPATH. SETUP_ADJUDICATION.md was registered before correcting only the parenthesis in versioned models_r2.py and the invocation path. Original source, GUARD/stdout/stderr and unsuccessful outcomes are retained; corrected fresh runs are not substitutes for those originals.

## Source/evidence protection and remaining gate

Both initialized exact views materialize522non-doc paths/modes,520protected against R5, with only reader/new test deltas. Every old149method/helper file and331full-file assert calls remain byte-exact. Removing only StreamObservationIntervals, its initialization and one call reconstructs the complete old reader bytes exactly; old InputTransitions, game/emitter/native/collector/workflow/privacy and all other engines remain unchanged. The supported constructor proposal was not applied. All178historical fixtures were populated before literal checks. Both source views are clean after all runs; the depth view exposes exactly one commit and shares immutable Git objects, not a self-contained clone/SDK reparse.

Original builder182manifest members/4,954,982bytes are directly verified against exact Git blobs, including retained compressed whitespace-check output and raw-byte handling. The additive query10members are independently bound, and the original handoff manifest is unchanged. Sealed R5's551members, actual R5/R4/R3 failures, incomplete R1 query and corrected R2 source remain untouched. No receipt corpus or SDK was copied.

Largest supported defect is the missing owner-derived local pop necessities above. This REVISE does not approve current R6, inherited R7, the whole reader, synthetic fixture/native faithfulness, actual207 replay, study/capability or any engine/API/proc/SDK/helper/CI/acquisition action. Root's prospective next repair branch was not inspected; it requires a separate exact freeze and registered assessment. No approval is inherited from the247/49/3060matches or previous binder/math component verdicts.
