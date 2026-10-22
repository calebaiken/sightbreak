# Independent M1 field-menu review

Candidate wins the baseline comparison for the declared field-menu keyboard-focus
correction. I independently reproduced the missing focus, inspected the product
and test diff, and ran real source-bound Linux exports with OS keyboard input.
After the test UID repair, I found no remaining blocker for this bounded
correction. This is an unblinded mechanical comparison with distinct outcomes;
it makes no aesthetic or Counter-Strike 2 parity claim.

I am `/root/menu_critic`, separate from the builder. I read AGENTS.md, the mission,
acceptance/progress/resume records, CLAUDE.md, parallel ownership guidance, the
original gauntlet-loop and no-ai-slop skills including eval.md, the project
gauntlet skill, the declared CRITERIA.md, builder baseline/candidate/regression
outputs and the actual diff. The existing broad mission gates remain open.

| Evidence | Baseline | Candidate |
| --- | --- | --- |
| Same actual-scene focus test | 9 checks, 3 failures: missing initial RESUME focus on all three opens | 30 checks, 0 failures |
| Exported Escape → Return | FIELD MENU has no focus outline; Return leaves it paused | RESUME has the existing gold focus outline; Return resumes on three opens |
| OS Tab / Shift-Tab | Not separately exercised natively | Complete forward/reverse four-action cycle, with raw screenshots inspected |
| Repeated close/open | No native repeat claim | Scene focus owner releases; three native opens return to RESUME |
| Existing input-mode regression | No independent baseline rerun | 31 checks, 0 failures |
| Focus loss/restoration with held W/LMB | Not separately exercised natively | Native focus loss pauses; restored focus remains paused; Return resumes with held inputs neutral |

The initial reviewed candidate was `8de7331927e21f15844e1928f4b17ed7ad5c9a4d`.
Fresh import exposed its omitted `menu_focus_test.gd.uid`. I reported it before
changing anything. Root supplied UID-only `aa0b0a4`; I cherry-picked it in the
detached review worktree, producing `6767e977ee886fe534350c43c35691e2dc7d9421`.
The diff against8de7331 contains only that test sidecar. Shipping main.gd bytes
remain identical (SHA256 `7ea405d9fe3bd934947693a58de817abff22a9bd6b7aea5e764abcde92a2e316`).
I made no implementation changes. The source-bound native receipts report clean
source for both executed exports.

The baseline export is exact `561d0cbba651514bfac96c50437a849d65843545`, game tree
`45b6c6ea9d3244700e324e90d6df4778ee28d18e`, executable SHA256
`3a0d35a55d6ddc1cb461b1bb1087b2f562ada61ae82b4355d189151e6020cc4f`.
The reviewed follow-up export is6767e97, game tree
`c17291675036f7a354dea1da5ea93b5865f78ea8`, executable SHA256
`8680ef47aab4e024eee0d5581e804fd4e08a76aa61a2cc2456df83c27f3c836b`.
The pinned engine was official Godot4.7.2, `ed1daf0bf`. Native logs identify Mesa
llvmpipe. These receipts qualify neither hardware performance nor controller
hardware.

In the final native candidate run I inspected the original1280x720 PNGs03–17,
including every forward/reverse focus position. Tab moves RESUME → SETTINGS →
EDIT TOUCH HUD → LEAVE MATCH → RESUME; Shift-Tab reverses that order. The visible
border follows the focused action, and the scene test separately checks the
focus owner and ui_accept routing. Two completed rendered frames precede each
final capture. This avoids the stale screenshot problem seen in the early
controller attempt.

The stock offline observer shows simulation tick40, elapsed0.6666667 and
remaining buy time14.3333333 before and after the paused stability interval.
After ordinary live begins, OS W/LMB are acknowledged as move[0,1]/fire=true.
Native focus loss pauses at tick928; restoring OS focus leaves tick928 paused
with the visible pointer and focused RESUME. Return explicitly resumes.
The final capture at tick954 still has physical W/LMB held (XQueryKeymap and
XQueryPointer), while authoritative consumed move is[0,0], fire=false and ammo
remains14. The scene regression covers the wider simulated mobile/controller
input policy. I did not activate SETTINGS, edit the touch HUD or leave the match
through its button, because those actions have wider effects than this correction.

Baseline native control passed in16.712s; candidate r2 passed in65.877s; final r3
passed in73.772s. Each client exits0 through the ordinary native close protocol.
The maintained native-log classifier reports no failure in these client logs.
The elapsed durations are trial records, not performance measurements.

All evidence is under `/workspace/sightbreak-menu-review/builds/menu-critic`:
`baseline.txt`, `candidate.txt`, `input-regression.txt`, the clean export receipt,
`native-baseline`, `native-candidate-r2`, and `native-candidate-r3`. Each native
folder retains original PNGs, raw video, native log, one-way stock trace,
OS action/command ledger and result. I inspected the PNGs and trace observations;
I did not watch every video frame. `COMMANDS.md` gives the exact top-level commands
and failed-attempt history; `native-candidate-r3/controller.py` is the actual final
controller. `screenshot-focus-observations.json` records original PNG dimensions,
hashes and border samples as an additional check. `sha256.txt` inventories retained
evidence files.

The first export used a state directory without the templates installed in the
setup state. A later redundant setup attempt hit ETXTBSY while the shared editor
was running. Both failures are preserved. Reusing the initialized state fixed
the environment. The first native attempt stopped because its input prerequisite
ran during the stock buy phase, when actor inputs are suppressed; its cleanup
also caused XIO and lacks result.json. It is retained as a failed observer run.
The second run fixes that prerequisite. The third adds capture freshness and widens its own observer budget from130 to
240s total, with up to120s rather than40s to reach the stock live phase. Its
successful73.772s run remains inside the original130s total. These are trial
controller budgets; no game behavior, product timeout or acceptance assertion
changed.

The largest remaining deficiency is physical input coverage: this proves Linux
OS keyboard events in Xvfb, while controller buttons/sticks, real desktop devices
and their latency remain unverified. Those need the corresponding hardware and
human observation. Wider keyboard journeys, Windows/macOS gameplay, complete
matches/objectives/progression, visual quality, mobile behavior and release
readiness were not reviewed. I did not run the full validate.sh suite or certify
any complete G1–G20 gate. Root must retain the UID sidecar and run its integration
checks on the final combined source before promoting this limited result.
