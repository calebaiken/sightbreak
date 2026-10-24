# CI repair follow-up — not a candidate pass

The failed Linux source is `2a026e61cabee3c66334066d45e92eb3ec6c2641`, run
[39880125007](https://github.com/calebaiken/sightbreak/actions/runs/39880125007).
Its 82/83 matrix result and both failed exported flows remain failed. This
collection copies completed local controls; it does not rerun or replace them.

## Repairs awaiting a new frozen Linux run

- Isolate matrix Git mocks from Python's shared `subprocess` module. The old
  Linux error came from `platform.platform()` consuming the Git fixture.
- Create and synchronize X11 close atoms before starting the exported ELF,
  require its advertised delete protocol, then request normal window closure.
  No process-kill or frame-quit substitute can pass.
- Use ordinary offline Field Menu pauses during OCR inspection of the original
  live HUD frames. Require visible `FIELD MENU` and `Training is paused` text;
  resume actual play for reload. Positive health and ammunition conservation
  remain mandatory. This is an inspection-paused flow, not continuous play.

The local maintained suites run **19 matrix + 14 UI + 6 HUD + 28 export-flow
tests**, all actual exit zero. They are pure/synthetic controls, not Linux/X11
or exported-game passes. Read their raw logs and source hashes under
`raw/maintained-unit-controls/`.

The independent critic ran those 67 maintained tests, 26 synthetic controller
controls and four protocol/layout controls. Read **both**
[REPORT.md](raw/ci-repair-critic/REPORT.md) and
[SOURCE_DRIFT_ADDENDUM.md](raw/ci-repair-critic/SOURCE_DRIFT_ADDENDUM.md).
HEAD advanced from the backend slice to the additive snapshot slice while the
critic sealed its report. All 22 reviewed source hashes and reviewed working
tree state stayed unchanged; this is not an exact-new-commit frozen campaign.
The failed aggregate drift receipt is retained. Actual Linux pause rendering,
Xlib behavior and completion-driven normal exits remain to be checked.

## Engine and generated UID custody

The old local engine disappeared after a restart; blocked pre-launch attempts
are not passes. Official Godot 4.7.2 was reacquired, its ZIP checked against
the published SHA512 before extraction, and its executable SHA256 matches the
previously frozen engine. Binaries stay external; sums, metadata and collector
are copied here. The first UID attempt's failure is explicitly a transcription,
not invented native output. A new isolated **one-script** editor import completed
with matching source bytes, process receipt and engine log. It generated
`uid://bfcad5gtqd8rv`; this does not validate the whole game or its performance.

## Publication audit

The first index audit found 18 raw input-component logs missing because of the
root log-ignore rule. A narrow parent ignore exception preserves the sealed
packet bytes and ledger. The second audit checks all **761 payloads** in the
completed backend and input-component packets against physical and Git-index
bytes, with zero mismatches. Both audit attempts are retained.

`COLLECTION.json` lists exact origins, sizes, hashes and omissions.
`SHA256SUMS.txt` covers every published file except itself. Nothing in these
tooling controls waives human, device, production or per-category 8.5 gates.
