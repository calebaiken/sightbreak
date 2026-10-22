# Visible LEAVE MATCH lookup

Declared before code changes, 2026-10-22. Baseline is the actual Windows journey
from [CI39723283770](https://github.com/calebaiken/sightbreak/actions/runs/39723283770),
frozen `dc2a198`. Builder branch starts at integrated root `e38ec3c`, retaining the
accepted settings transaction and later workflow, original-PNG and OCR-resource
work. The baseline offline controller is unchanged between those sources.

The journey reaches a living, focused player after settings resume, then fails
`Native UI text not found: LEAVE` at driver 87.375 seconds. Its retained final
`ocr-current.png` visibly shows FIELD MENU, “Training is paused.” and LEAVE MATCH.
The final PSM11 TSV OCR exits zero; the native Windows stdout/TSV was not saved.
The source requires one exact uppercase LEAVE token. Actual Windows tokenization
or misreading is therefore unknown; no missing-menu, clipping or layout defect
has been established.

Required evidence and gates:

- Preserve the unchanged actual final PNG, command/action/state receipts and
  failed outcome. Reproduce the production image transform and lookup locally,
  saving raw OCR text/TSV, arguments, exit and image identity. Linux pixel replay
  is supporting analysis, never native Windows acceptance.
- Choose a correction only after the replay identifies a concrete observer
  weakness supported by those pixels. The complete visible control label must
  remain readable and unambiguous. Do not replace visibility with a guessed
  coordinate or accept a hidden/removed control.
- Require the actual menu heading and intended control as applicable; preserve
  normal physical native input and the rendered/state return-to-menu check.
  Keyboard navigation is permissible only if the actual controls and resulting
  rendered/state transition are independently exercised.
- Preserve the accepted living-player, actor/round/weapon/ammunition, focus,
  frame, pause and source-identity guards. Keep stock starts/rules and simulation
  speed. No injection, teleport, invulnerability or observer-side game mutation.
- Retain the existing whole-flow 300-second deadline, external OCR 20-second
  ceiling and every existing stage deadline. Any new observation work must fit
  those limits; no unlimited retries or silent skip may produce acceptance.
- Replay ordinary positive menu/control frames and actual settings/game/menu
  negatives. Explicitly label altered copies with the intended control or its
  text removed. Preserve strict ammunition/health/life negatives.
- Run actual Linux exported input through the changed leave transaction when the
  shared native lane is available, with original PNGs, trace/actions, exact
  source/export and clean process ownership. A focused probe cannot stand in for
  the complete settings-restart/focus journey or for Windows input.
- Have an independent critic inspect source, original pixels, controls, budgets
  and native receipts. The builder cannot approve its own correction. The exact
  Windows full journey remains required after integration.

Current limit: Windows native OCR stdout is absent. A Linux replay can expose an
observer failure on identical pixels but cannot reconstruct the exact missing
Windows token stream. No code correction has been selected at this checkpoint.
