# Independent dry-primary comparison verdict

**Winner: candidate. PASS for the narrow dry-primary return correction at
`8e8d13e7dbf427b464519868d38a9c40aa732594`.** Actual candidate decisions avoid
known-dry primary equips and the resulting empty reload/fallback loop, while
the declared unaffected controls remain correct. This is a comparison of named
source-bound outputs against the actual baseline, not a blind comparison or
proof of complete bot quality.

Baseline source is `b0635964c6b819ed41a9568afdb0b5068c3d5577`. Builder raw/report
commit `6a0ef573c67df73c574f525bd1461176d3995241` retains both sides and the
required regression outputs. I verified all 20 raw log, controller, receipt and
source-snapshot files against that immutable commit. Runtime source snapshots
are clean and identical before/after each run. The common fixture remains
SHA-256 `059a49bdf1e755a049e0fa4a904d303eb5fc9ce1fd05cbfc993ee9881aa46863`.

## Actual comparison

| Actual output | Baseline | Candidate |
| --- | ---: | ---: |
| Common cases / authority steps / assertions | 84 / 48 / 590 | 84 / 48 / 590 |
| Failed assertions / engine exit | 40 / 1 | 0 / 0 |
| Idle sequence, each profile: dry equips / empty reload requests | 1 / 7 | 0 / 0 |
| Alternating normal/hard, each: switches / dry equips | 8 / 4 | 0 / 0 |
| Alternating easy: dry equips / empty reload requests | 1 / 7 | 0 / 0 |

The independent recomputer checks each of the 84 case outputs and all 48 step
transitions against expectations derived from the registered scenarios. Each
side satisfies 1,974 observable checks. Baseline's exact 40 failure labels are
expected and retained; it remains a failed fixture. Candidate has zero failure
labels and zero mismatches. Pairing actual case outputs finds exactly the
intended 21 primary-request changes and three coupled reload changes. All other
logged case fields match, and the other 63 requested-weapon controls remain
unchanged.

Known dry, clip-positive, reserve-positive and missing-state controls pass for
every primary and difficulty. Active stale-cache controls, ownership, selected
priority cases, interacting return, close fallback with both reserve values,
easy fallback policy, the 20 m boundary, loaded-primary, unowned-sidearm and
interacting-defuser controls match their declared outcomes. All six candidate
sequences retain loaded sidearm ammo/reserve 15/60, total ammo 75, zero reload
and deploy timers, and zero shots. No correctness regression is visible within
these controls. Full protected-state preservation relies on the source-reviewed
fixture assertions because those complete snapshots are not logged.

The candidate's existing bot AI regression emits its success marker and exits
0 in 1.814193547 s. Its squad regression exits 0 in 33.359080858 s, logging
960 samples and 2,722 assertions with zero failures. I independently grouped
all 960 samples by difficulty, team, scenario and slot: all 480 corresponding
squad pairs have identical output dictionaries and the expected actor IDs.
These support the existing regression scope; they do not recreate every
internal regression assertion from raw data.

I verified 41 additional source/hash/receipt/pair conditions. The three
candidate runs use exact source `8e8d13e`, distinct private state paths, pinned
Godot 4.7.2, 120-second wall deadlines, no timeout and no engine error. The
fixture itself exits normally in 1.251822971 s. Observed native PID/SID/start
identities are 5753/5753/417689, 5831/5831/418418 and 5887/5887/419211. Terminal
scans contain no same-session member or recognized Godot process. No cleanup
signal was needed. Source and raw hashes are retained in the accompanying JSON.

The recomputer also rejects seven retained derived-log falsifiers plus a
strict Boolean-type falsifier. These are pure oracle checks, not extra engine
runs. They support the parser's failure behavior; the actual source comparison
and recorded gameplay outputs support the verdict.

## Largest remaining deficiency and boundaries

The largest remaining bot-quality deficiency is absence of representative
complete-match evidence that this bounded ammo-selection improvement helps
ordinary play without broader reliability or balance regressions. This fixture
injects visibility and directly consumes actions without the full movement,
perception or objective loop. The native outputs do not explain a historical
journey timeout, establish CS2 parity, measure performance, or close G1/G2/G17.

The largest observation gap is missing full protected before/after snapshots
and inventory/ammo-store inputs in the raw JSON. Authority predicates beyond
logged ammo/weapon/timer fields depend on the reviewed fixture assertions and
exact-source binding. Explicit all-three-loaded and two-dry/usable-SMG priority
examples are absent; the candidate retains the original literal priority list
in its three-line guard. The source review found no broader policy change.

Cleanup is qualified to observed normal exits and terminal SID/Godot scans.
The controller does not establish recursive escaped-descendant coverage or
timeout/error-path cleanup. The maintained registration is source-reviewed,
but a whole-source maintained aggregate and exported-client journey have not
run on this candidate. Those gates remain open for root's combined-source work.
