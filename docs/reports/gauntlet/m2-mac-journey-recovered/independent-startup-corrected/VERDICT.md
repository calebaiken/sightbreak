# Source-only approval of corrected window readiness

Approve exact source freeze `3efe35d1ee565dc8e654daa2d0b52481cc7ce5b6` for the
bounded ordinary Mac controller correction. The review used its own sparse
worktree and branch at evidence commit `f412dfeb65775c28536c2c8a36a98150f2919bd9`;
the tested source bytes match the freeze. No native API/input, engine, OCR,
export, CI dispatch or platform gameplay process was run.

The blocking late-window counterexample is fixed. Discovery and the real window
guard share `owned_visible_windows()`, selecting the exact PID with
`onscreen is True`. Every guard requires exactly one selected row, the pinned
window ID and the original bounds with the inherited half-point tolerance.
Fresh focused capture and `pin_for_input()` reach this guard through
`require_target()`. Label, fire, reload, Escape and other input-down methods use
that same target guard. Complete current rows are traced before rejection.
Foreign or hidden extra rows cannot create ambiguity, and valid single-window
startup still completes the synthetic journey.

Independent evidence retained here:

- All 70 maintained pure tests and four aliased-temp commands pass.
- The original `independent_controls.py` is byte-identical to rejection `bfe7b5a`
  (SHA-256 `03c18b0f8ff5e432f1b97f051b3daf2accdfde72f3d69bfed0146702fcafba67`).
  All 11 unchanged controls pass. The completed replay took 176.161 wall seconds
  under a 600-second test-wrapper limit; the runtime's 60 mocked-second menu
  deadline is unchanged. The repeated-trace cost belongs to this synthetic test.
- The direct pin falsifier now reports an ambiguity error, `pinned=false` and
  zero event attempts while retaining both actual mocked rows. The full synthetic
  case reports `deployed=false`, `pinned=false` and `reported_pass=false`. Its
  complete 1,839,007-byte trace is retained losslessly as
  `late-ambiguity-counterexample.json.gz`, with original/archive hashes and a
  concise result in `late-ambiguity-summary.json`.
- Three additional actual-method control groups pass: every owned input-down
  method rejects ambiguity before event allocation; a single visible window
  with hidden/foreign/nonboolean decoys remains valid; permission and private
  isolation failures cannot pin. The existing unchanged controls verify the
  pre-pin event barrier, event release, permanent pin, late menu/focus rejection,
  persistent splash, later geometry/disappearance and retained decision rows.
- Source and evidence audits pass. The whole Deploy-through-teardown section and
  budgets match the accepted prior runtime. Game source, accepted menu adapter,
  menu driver, Swift capture helper and workflow are unchanged. All 21 original
  rejected-review files match `bfe7b5a`; all original native failure-index files
  match their recorded hashes. All 56 builder evidence-index files match. The
  builder's incomplete 60-second replay wrapper remains retained separately.

No further blocking source finding was found in this scope. The largest remaining
gap is actual behavior of these corrected bytes on ARM macOS. Original run
`39906639650` at `b2e0293` stays failed before any CGEvent: its actual screenshot
shows the Godot splash, later guard rows were absent, the public failure-close
request timed out and SIGTERM removed the client. A particular resize or window
replacement cause is still unknown. This review does not certify that cause is
cured, actual input delivery, gameplay, 1280x720 rendered frames, ordinary native
teardown, complete Mac journeys or an 8.5 quality gate.

## Conditions for one future ARM attempt

1. Root must freeze and independently review the intended combined source, record
   its exact commit/game tree/content and validation hashes, and verify that its
   Mac controller, tests, adapter, capture helper and workflow retain the reviewed
   bytes. Any relevant integration change needs fresh affected source controls.
   This component approval does not approve an unseen combined commit.
2. Run the maintained pure controls and the preserved ambiguity falsifiers on that
   exact combined source. Bind a new native export and its manifest to the same
   clean source; use the unchanged same-source native preflight and menu gates
   before the ordinary component. Do not reuse earlier-source native receipts.
3. After those conditions pass, root may release one exact combined-source ARM
   retry. Keep the requested 1280x720 command, graphics defaults, exact app/PCK,
   private/default userdata checks, zero-event startup discovery, fresh focused
   menu and metadata agreement, one permanent pin, one 60-second menu deadline,
   one five-second focus budget and every gameplay/cleanup limit. Preserve all
   new raw outputs and all prior failures. Stop for review after that one attempt.
4. A fresh independent review must inspect the actual new screenshots, authority
   observations, event/window traces, source/payload/profile attestations and
   cleanup before granting any native component acceptance. Until then gameplay
   remains unverified and the platform/quality gates remain open.
