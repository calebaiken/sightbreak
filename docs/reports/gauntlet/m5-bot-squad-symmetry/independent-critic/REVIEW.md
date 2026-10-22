# Independent M5 bot habit review

Accepted for the six declared squad-position behaviors. The candidate produces
equal complete commands, tactical roles and destinations for corresponding
squad slots, while the baseline does not. This is a deterministic habit
correction; it does not close G2 or qualify competitive fairness.

Reviewed on 2026-10-22 by a fresh Codex critic, separately from the builder.
I read the declared PLAN, actual source, original Claude commit, retained failed
iterations and raw engine outputs. A second read-only adversarial auditor also
inspected the fixture and product scope. This was an identified correctness
comparison, not a blind visual judgment.

| Source | Exact identity |
| --- | --- |
| Baseline gameplay | `42ff3dc3d1f52e40da2120b5bcee39a15b86e1ca` |
| Executed baseline checkout | `643d022338b5df196b007e67fe3e5a40e3029a4c`, with the final oracle copied in |
| Candidate product | `c2b3dedd41c386c909aead298017cdfdb516434d` |
| Independent execution | `1b88349ea2e58bcecc933abac53f228f6a39cbdf` |
| Final oracle SHA256, both checkouts | `0f2ce7e26d85405c633b4cda6807f8a2f36acd5f3fdb2766ea99238ab907dc77` |
| Engine | `4.7.2.stable.official.ed1daf0bf` |

The baseline checkout contains the preregistered fixture commit; its gameplay
scripts equal the named baseline. It intentionally runs the final test as an
overlay in observation mode, whose exit zero preserves failing output rather
than declaring success. The candidate bot source is unchanged between product
`c2b3ded`, full-suite source `8ef757e`, and independent source `1b88349`.

Claude's adapted bot source at `06092d0` is byte-for-byte equal to the bot source
in PR28 commit `0871bc92b014fdb020cb1ac681fe70637f6cf6cd`. That contribution
preserves Claude authorship and Claude Sonnet 5.5 co-authorship. The two later
sine-phase changes are separately attributed. The authority shuffle `6ed3ee0`,
its tests, and PR26 arena changes are absent. `match.gd`, `actor.gd` and
`arena.gd` have identical baseline/candidate Git blobs. No renderer, mesh, HUD,
audio or protocol file changes are introduced by this candidate.

I executed the final oracle and eight supporting steps serially in an isolated
sparse worktree. Every step passed with the same HEAD, unchanged tracked game
and script files, and identical before/after source hashes. The oracle passed
in 33.051 seconds. The supporting steps were import, bot AI regression,
authority order (178 checks), match (75), actor (73), weapon integrity (28),
hit volume (40) and state privacy (55). The raw receipts are
[focused-receipts.json](focused-receipts.json); these counts describe coverage
and are not bot quality scores.

| Final actual engine output | Baseline | Candidate |
| --- | ---: | ---: |
| Samples | 960 | 960 |
| Oracle assertion failures | 300 intentional | 0 |
| Unequal full command/role/destination pairs | 181 / 480 | 0 / 480 |
| Idle samples still moving | 0 / 60 | 0 / 60 |

The independent parser requires the complete expected Cartesian sample set:
five slots, both assigned team roles, easy/normal/hard, sixteen states and both
actor groups. It compares all ten emitted input fields plus role and destination,
without normalizing an emitted command. Its full unequal-pair records are in
[paired-comparison.json](paired-comparison.json), with both raw final logs.

The baseline differences are close combat 30, long combat 18, unsticking 30,
jump-stage recovery 30, idle scan 24, travel 13, below-threshold recovery 13,
carrier 13 and smoke 10. The latter navigation/objective differences include
defender anchor selection. Candidate close combat has two habitual crouchers per
five actors in each squad; normal/hard attacker approach has three smoke users
per squad, while easy has none. Every corresponding normal/hard defender slot
selects the same anchor. These are intended equalities with retained variation
between slots.

The final fixture also checks actual enemy acquisition before reaction firing,
difficulty-specific fire cadence, long-range braking, utility distance/resource
gates, carrier utility, smoke-used transition/repeat suppression/reset rearming,
staged recovery, plant/defuse stopping and defuse-cover selection. Decisions
leave health, ammo, reserves, credits and utility resources unchanged; inactive
and dead actors remain inert. Protocol remains 6 and offline ranked payloads
remain empty. I found no blocking regression in the reviewed scope.

Two earlier fixture limitations remain in the builder's retained history. The
first long-range target was 30 m away, outside easy vision at 28 m; the final
target is 26 m away. The r2 logs had 26 moving samples labeled idle; they are
superseded by the stable-plan fixture and its explicit zero-movement assertion.
The independent r2 recomputation agrees with its 172 unequal baseline pairs,
279 baseline failures and zero candidate differences, but that fixture did not
fully establish idle scan coverage. Those numbers are not the final result.

The maintained `validate.sh` run completed at exact source `8ef757e`, before the
fixture-only additions in `1b88349`. I inspected its actual raw completion and
bot lifecycle result: ten rounds, 7:3, 60 kills, halftime, one result report and
`plant_observed=true` over 325.9 simulated seconds. It is one stock lifecycle
observation. Rendered visibility, native Windows cases, catalog drift without
backend Python and optional backend SQL were not established by that run.
The final independent focused run does not re-attest the entire maintained
suite to a different HEAD.

The largest remaining gap is representative full-match bot quality. Isolated
fixtures reset shared randomness and team memory and deactivate the rest of
the roster; the real roster loop still shares randomness and same-tick reports.
Those fixtures cannot establish match fairness, sustained objective reliability,
navigation quality or cooperation. The optional eight-match set was omitted
before its first sample, so no paired-match result exists. Its retained future
tool records source identity only after a run; before/after source and harness
guards are needed before using it for exact-source measurement claims. Rendered
presentation, human play and device behavior were not judged here.

Recompute the retained final comparison with:

```sh
python3 docs/reports/gauntlet/m5-bot-squad-symmetry/independent-critic/inspect_samples.py \
  docs/reports/gauntlet/m5-bot-squad-symmetry/independent-critic/baseline-final.log \
  docs/reports/gauntlet/m5-bot-squad-symmetry/independent-critic/symmetry.log
```
