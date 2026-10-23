# Dry primary return candidate

The candidate skips an owned primary with a recorded holstered clip and reserve
of `(0, 0)`. A sidearm holder keeps its usable weapon instead of returning to a
known dry primary. Missing records retain equip defaults, reserve-only primaries
remain eligible, and the literal rifle > marksman > SMG order is preserved.

The entire product delta is three added lines in
`game/scripts/gameplay/bot_ai.gd`, commit `bd4ea03`. Maintained registration is a
separate commit, `8e8d13e`, in `scripts/validate.sh` and
`scripts/run_native_regressions.py`. All candidate runs used exact source
`8e8d13e7dbf427b464519868d38a9c40aa732594`. The unchanged baseline used
`b0635964c6b819ed41a9568afdb0b5068c3d5577`.

## Actual measurements

| Run | Result | Exit | Elapsed |
| --- | --- | ---: | ---: |
| Common baseline | 84 cases, 48 authority steps, 590 checks, 40 failed expectations | 1 | 1.269 s |
| Common candidate | 84 cases, 48 authority steps, 590 checks, zero failures | 0 | 1.252 s |
| Existing bot AI regression | `BOT_AI_REGRESSION_TESTS_OK` | 0 | 1.814 s |
| Existing squad symmetry | 960 samples, 2,722 checks, zero failures | 0 | 33.359 s |

The common fixture and its UID were byte-identical for both runs; the fixture
SHA-256 is `059a49bdf1e755a049e0fa4a904d303eb5fc9ce1fd05cbfc993ee9881aa46863`.
Every run had a 120-second wall bound, pinned Godot 4.7.2 and a separate state
directory. The elapsed times describe these headless runs, not game performance.
No engine error line or timeout occurred.

Baseline normal/hard alternating-visibility sequences each made eight switches,
including four dry equips. Each no-target sequence made one dry equip followed
by seven reload requests with zero reserve. Candidate sequences across all three
profiles made zero switches, dry equips and reserve-empty reload requests. Both
sides emitted zero shots in these one-tick sightings; reaction controls remained
in effect. Full rows and failures are retained under `baseline-r1` and
`candidate-r1`, with the existing regression outputs in `candidate-bot-ai-r1` and
`candidate-squad-r1`.

## Independent review and evidence limits

Fresh source review `d5df016` approved the common fixture before baseline runtime.
Independent baseline recomputation `7c56ad0` checked 1,974 observable predicates
and the exact 40 failures. Candidate source review `4f39a33` approved the exact
three-line guard and both maintained registrations before candidate runtime.
Those reports live on `review/m5-dry-weapon-recovered` under
`docs/reports/gauntlet/m5-dry-weapon-recovered-independent`.

Final independent actual-output review `f947350` picks the candidate as better
and passes this narrow correction. It binds the raw/report commit `6a0ef57`,
recomputes each side's 1,974 observable predicates, verifies the intended 21
primary-request and three coupled reload changes, and retains 63 unchanged
request controls. All 480 independently grouped squad pairs match. The report is
`docs/reports/gauntlet/m5-dry-weapon-recovered-independent/FINAL_REVIEW.md` on the
separate review branch. This accepts the bounded correction at `8e8d13e`.
Raw JSON omits full protected snapshots and input inventory/ammo-store values;
deep authority comparisons depend on the retained, source-reviewed fixture
assertions. The matrix also omits all-three-loaded and
dry-rifle/dry-marksman/usable-SMG priority cases. Literal priority is preserved in
source. Visibility is injected, and the interaction controls cover selected
branches. This evidence establishes neither complete perception/objective
coverage nor full-match balance or the cause of a historical journey timeout.

Each receipt binds the command, source/hash snapshots, private state, observed
engine PID/session/start tick, exit, raw log hash and terminal scan. All observed
engines exited normally, and no same-session process or recognized Godot process
remained in a terminal scan. The controller enumerates session membership; it
does not qualify recursive escaped-descendant discovery or timeout/failure
cleanup. No general cleanup claim follows from these normal exits.

The broad maintained suite, exported-client journey and representative complete
matches have not run on this candidate. Whole G1/G2/G17 remain open. The largest
remaining bot-quality gap is representative full-match evidence; this bounded
selection fix does not close it.
