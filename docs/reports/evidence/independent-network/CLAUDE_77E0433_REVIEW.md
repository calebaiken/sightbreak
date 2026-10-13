# Independent follow-up review: Claude PR #1 at 77e0433

Reviewed 2026-10-13. Exact head: `77e0433166b71c9de1456ef8639ce125d1b92029`. Detached read-only worktree: `/workspace/sightbreak-claude-latest-review`. No tracked file was modified. No PR comment, approval, or merge was submitted by this reviewer.

## Recommendation: request changes

The protocol and body-volume follow-ups are sound in the checks below. The reported all-green HUD result is **disputed**: the maintained test still fails ten Unicode row-visibility assertions, both headless and in the native renderer. Fix the remaining fallback-font row-height defect before representing PR #1 as integration-green. Independent Codex modules can continue stacking on this head with the unresolved HUD failure explicitly recorded.

## Commits inspected

The seven commits after previously reviewed `cf9a630` are:

| Commit | Change | Independent conclusion |
|---|---|---|
| `ff41188` | Grapheme-aware truncation | Improved boundary correctness; maintained grapheme checks pass here. Does not fix row height. |
| `fc52e68` | Tangent capsule misses | Correct against maintained tangent probes. |
| `a84b208` | First hello decides, numeric protocol and accepted-type validation | 8/8 hostile-process checks pass; original fractional and retry probes now reject. |
| `5407325` | 64-bit capsule spans | Maintained 4000-ray comparison passes; independent foot grid remains exact. |
| `d0278f0` | Limit generic stacked combining marks | Specific stacked-mark checks pass. Does not fix CJK fallback metrics. |
| `24ede81` | Reports and evidence | Claims are not accepted as independent results; HUD all-green claim fails reproduction in this environment. |
| `77e0433` | Probe versions follow PROTOCOL_VERSION | Correct integration improvement for subsequent protocol bumps. |

Read both audit documents and the new Codex response. The graphics-production branch `498311e` contains this PR head through merge `f519e7b`; its merge base with this review head is exactly `77e0433`. Its new art was not modified or reviewed as part of this focused task.

## Blocking: Unicode kill-feed rows are still clipped

`game/scripts/main.gd:662–666` computes the frame height from a Latin `Ag` Label. The frame clips its children. Actual CJK fallback glyphs make each Unicode row taller, so the fourth row extends outside the frame. Grapheme truncation and generic combining-mark filtering do not change this cause.

Independent evidence on this exact head:

- Maintained headless HUD: **1325 checks, 10 failures**.
- Maintained native HUD: **1331 checks, 10 failures**, including six screenshot-save checks. The native run completed and exited nonzero for the assertions.
- All five sizes fail for the Unicode case at both 100% and 130% text: 960×720, 1180×820, 1280×720, 1560×720 and 1600×720.
- At 100%: frame y=53, height=113, bottom=166; fourth row y=146, height=28, bottom=174: **8px clipped**.
- At 130%: frame bottom=197, fourth row bottom=203: **6px clipped**.
- Label measurements at font14: Latin20px, CJK22px. At font18: Latin26px, CJK28px.

Native screenshot visually inspected: `claude77-hud-native-complete/1560x720-killfeed-unicode-130.png` (an earlier identical-scope capture was inspected before the full rerun completed). The fourth row is visibly truncated. Exact file/source hashes: `claude77-source-evidence.sha256`.

Please derive the four-row frame height from actual row/font-fallback metrics while preserving width isolation, and rerun the native/headless matrices. A fixed extra pixel allowance remains font-dependent. Keep assertions intact.

## Confirmed fixes and regression results

| Check independently executed | Result | Evidence |
|---|---|---|
| Weapon integrity | 28/28 pass | `claude77-weapon.log` |
| Hit volumes, tangent and long-range cases | 40/40 pass | `claude77-hit-volume.log` |
| Original independent lower-leg grid | 1468 physics hits = 1468 authoritative hits, zero added body cells, both standing/crouched | `claude77-independent-hit.log` |
| Original eye-to-foot corner ray | Both physics and authority miss, both stances | `claude77-independent-hit.log` |
| Maintained real-process handshake hardening | 8/8 pass | `claude77-handshake.log`, `claude77-handshake/` |
| Original fractional2.9 hostile peer | Rejected; zero connected/authenticating peers or actor slots after7s | `claude77-adversarial/fractional.*.log` |
| Original reject99 → retry2 on same peer | Rejected; zero connected/authenticating peers or actor slots after7s | `claude77-adversarial/retry.*.log` |
| Compatible raw peer without join RPC | Still connected after26.017s, zero actor slots | `claude77-adversarial/silent.server.log` |
| Diff whitespace check | Pass | `git diff --check cf9a630..77e0433` |

Handshake scenarios include mismatch spam (one reply, drop0.52s), fractional/huge numeric input, rejected-then-good, good-then-bad, hostile-server hang-up, rejected reply discarded by immediate hang-up, and non-boolean accepted. Rejected cases emitted one server rejection and no server errors; good-first stayed admitted. The fixes do not establish account authentication by protocol alone.

## Outstanding risks and classification

- **Pre-existing, verified:** an admitted compatible raw peer that never sends join remains connected past26s. The first-hello change does not add post-authentication admission timeout. Codex PhaseD owns this hardening.
- **Pre-existing, code-confirmed / runtime-unverified on this head:** account-ticket consumption precedes duplicate-connected-account and available-slot checks. A compatible admission rejected for those reasons can consume a one-use ticket. Full-server/duplicate account admission deserves an isolated PostgreSQL reproduction and explicit lifecycle policy.
- **Preserved architecture:** version checks occur in raw SceneMultiplayer authentication before `_connected` sends the gameplay join RPC. No newly introduced path consuming an incompatible client's account ticket was found. The account/PostgreSQL and six-pair version matrix were not independently rerun in this focused follow-up; those must be run on the final integration branch by the lead engineer. Prior results do not substitute for that final-head run.
- **Pre-existing competitive problems:** hidden-state exposure, lack of continuous movement interpolation and idle admission remain present in this Claude head. They are handled by the separate Codex stack; this PR alone is not competitive/production readiness.
- **Existing product decision:** drawn head/helmet hit volumes materially change headshot area relative to0.3.0; crouched visible helmet partly exceeds the old capsule. These are already acknowledged in Claude's response and predate these seven follow-up commits. The new precision changes do not introduce the balance decision.
- **Unverified:** physical-device FPS/thermals/touch, human gunplay feel, encrypted Internet transport, external security audit, production readiness. No 8.5 score is inferred here.

## Integration guidance

Retain the new `_handshake_seen` and strict `_hello_protocol` behavior when integrating Codex protocol3/4/5 changes. Keep the protocol constant appropriate to the final message contract. Re-run dynamic handshake probes against that exact constant. Preserve both seen/drop cleanup and any new Codex peer lifecycle cleanup on disconnect and authentication failure. Actor hit-span edits are separate from movement extraction and should both remain. Do not resolve actor or match integration by taking an entire file from either branch. Preserve Claude's visual contracts and art branch.

## Exact environment and commands

Debian GNU/Linux13.6, Linux6.18.44, official Godot4.7.2 `ed1daf0bf`. Native rendering: Xvfb`:99`, OpenGL4.5 compatibility, Mesa25.0.7, llvmpipe LLVM19.1.7. This is desktop software rendering, not mobile GPU evidence.

From the detached worktree, using external state/evidence paths:

```sh
scripts/godot.sh --headless --script res://tests/hud_overflow_test.gd
scripts/godot.sh --headless --script res://tests/hit_volume_test.gd
scripts/godot.sh --headless --script res://tests/weapon_integrity_test.gd
scripts/test_handshake_hardening.sh <external-evidence-dir>
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 scripts/godot.sh --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/hud_overflow_test.gd -- --capture-dir=<external-evidence-dir>
```

An initial native run timed out at95s after reproducing9 failures and saving6 screenshots; it was not counted as a completed suite. The rerun used a180s cap and Dummy audio, completed with1331checks/10failures, and is the native suite result above. Font/geometry probes and original independent handshake/foot-grid scripts are retained alongside the logs for reproduction.
