# Source candidate frozen; native result unverified

Frozen source/workflow is `bd9ac47` on `codex/m2-mac-journey-recovered`, based on
published `917b143`. Preregistration is `52871a2`; the first recoverable draft is
`7f54901`. This is reconstructed new work. No missing pre-interruption Mac source
or raw gameplay output was recovered.

All 57 pure tests pass: 14 new helper groups, seven new complete mocked-controller
falsifier groups, and the original 11 menu / nine focus / seven saved-screen /
nine preflight groups. Compilation and `git diff --check` pass. The exact commands,
raw outputs, durations, output hashes and tested source-file hashes are in
`pure-tests-r2/results.json`. These tests ran the frozen code with untracked report
files present; `source_dirty=true` in that receipt is retained. The game content,
validation hash and all five tested source files remained unchanged. Earlier draft
outputs in `pure-tests/` remain intact; they precede the final schedule corrections.

The new mocked controller accepts its synthetic complete schedule and rejects
stale samples, no ammunition effect, absent fire/reload frame fences, missing or
early reload, death during native capture, wrong rendered ammunition, a successful
helper returning after its original deadline, delayed OS acknowledgements, forced
cleanup, changed payload/source/default userdata, leaks and refused ordinary close.
Every process, permission, screenshot and authority sample in those controller
tests is mocked. Their pass is source readiness only.

Independent draft criticism identified two defects in `7f54901`: a late successful
helper could exceed its stage budget, and OS acknowledgement could extend the
original fire holds. `bd9ac47` gives helper calls explicit post-return deadlines,
keeps each LMB hold/release slot at one second / 0.35 seconds including OS receipts,
and fixes reload completion's 15-second deadline before R-up acknowledgement.
The critic retains the rejected draft's reproductions separately. Final independent
source approval is pending; the builder does not approve this component.

`scope-audit.json` compares all original tracked scripts and the game tree to the
base. Every original script byte is unchanged; the game tree is unchanged. All
original workflow lines remain in order. The workflow adds only an ID to the old
Mac menu step, two new ARM-only test/control steps and the narrow ordinary journey.
Original Windows/Linux journeys, objective/full-match commands, host matrices,
stage budgets, native regression suites and strict leak gates remain intact.

The native isolation route copies the exact `.app` and adds only its executable
sibling two-value userdata override. `--main-pack` was rejected as an assumed
route because pinned upstream source disables path overrides in stock templates.
Actual override support, private `user://` log creation, Mac gameplay Vision text,
CGEvent gameplay delivery and clean teardown remain UNVERIFIED. A failure in any
of those gates must remain a failed or blocked attempt with original raw evidence.
No engine, export, service or CI run occurred while building this candidate.

Root owns execution release and the single native CPU lane. After independent
source acceptance, freeze the exact combined source, export it and obtain the
same-source ordinary native preflight/menu results. The additive ARM workflow then
runs `verify_macos_ordinary.py` with the original 300-second total and registered
stage bounds. The native run needs a fresh independent raw-output and screenshot
review. This component cannot close the full Mac journey, objectives, complete
match, restart persistence, Intel, physical-device, human-play or CS2 gates.
