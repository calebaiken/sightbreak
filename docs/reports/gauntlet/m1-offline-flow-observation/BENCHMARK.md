# Native offline observer correction

Status: candidate work; independent review and native reruns pending.

Source baseline: `6a0d8d5d85b4fb37943903886982f51b4ed230b0`.
Reference: actual exported clients from [CI run 39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860), not a fabricated HUD or simulated native result.

## Windows ammunition pixels

Windows job `119607694071`, QA artifact `12398666385`, SHA-256
`8144fa7380fd5a649d8077570d982fe2994888a7a97601f1d67f2227077f1897`,
failed at `07d-explicit-resume.png`. The saved native client pixels visibly show
`SMG 30 / 120`; the existing broad PSM 6 ammunition crop returns grenade labels
and no ammunition pair. Earlier reload, plant, defuse and full-match native gates
passed in this run. This correction does not claim those passes as new results.

Predeclared checks:

- Run the actual reader on the unchanged failing screenshot: require 30/120.
- Preserve the ammunition pairs in every ordinary-game capture supplied by this
  Windows attempt, including the real fire decrement, reload and weapon switch.
- Reject the actual menu and altered copies with health or ammunition removed.
  Altered images are negative controls, never native capture evidence.
- Keep health/life checks, external OCR deadlines, ordinary pause protection,
  round/context checks and whole-flow 300-second deadline unchanged.
- Record per-image OCR time, command, raw text and exit status. Each invocation
  must remain inside its existing 20-second cap. This is observer timing, not a
  gameplay performance or responsiveness benchmark.

## Linux focus-release acknowledgment

Linux job `119607694327` failed at `Fresh W press moves actual player after focus
recovery`, after the settings restart, held-input safety and explicit resume
steps. Its 47.9 MB QA archive exceeds the available 32 MiB transfer limit;
the official artifact redirect was denied by network policy. Preserve the
accessible actual job-log failure and label native raw-image review unavailable.

The old release predicate requires neutral movement/fire, which already holds
while the focus-release guard blocks held inputs. Diagnostics publishes before
the controller polls physical release. A fresh observation therefore need not
acknowledge that the controller consumed the release.

Predeclared checks:

- Reproduce this ordering using the real Godot controller and physical-key input
  state: a release followed by a new press before a controller tick must leave
  the safety guard engaged; the old neutral predicate can already be true.
- Expose the existing guard in the opt-in read-only offline UI snapshot. Require
  an actual guard-clear observation before sending the fresh movement press.
- Preserve held W/LMB suppression, explicit resume, actor/round/life checks,
  movement requirement, ten-second release/movement budgets and all game rules.
- Test missing/engaged guard state cannot satisfy the new release predicate;
  perform an actual exported Linux flow when a clean source-bound build exists.
- Windows full-flow and hosted Linux timing confidence require new native runs;
  a source-level ordering reproduction alone cannot establish either pass.

The builder supplies evidence and cannot approve this candidate. No blind A/B
is appropriate for a deterministic OCR correction or release-ack correctness
check; the critic must inspect the actual pixels, source and measured outputs.
