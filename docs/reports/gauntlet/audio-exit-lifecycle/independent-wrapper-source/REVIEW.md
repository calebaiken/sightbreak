# Independent acquisition wrapper source review

Verdict: **REJECT wrapper SOURCE** at exact
`90d3baa4efa22001f3b6fd500f545eb4328f96bf`, preregistration `57e5921`, branch
`codex/audio-exit-lifecycle-20261023`. Three retained independent counterexamples
return exit 0 with `passed=true` and `acquisition_integrity=true` despite a
current strict raw-log failure or mismatched private-state archive. Do not select
the actual diagnostic from this freeze.

This verdict covers only the new Linux acquisition wrapper. Observer/analyzer
policy `73cdfc2d8d6956eef1cd2e14e1461b93152afc80` retains its separate SOURCE
acceptance `146dc176f923568f34102e7a73742080f00a0db5`. `source-audit.json` binds all
425 game/script paths present at that accepted freeze to reviewed and local Git
bytes; all match. Only the wrapper and its maintained test file were added to
those code trees. The retained original controller has the preregistered SHA-256
`43dfdeae51aaa95dbb43aeb33125c772688f50e604cc471c8b4ba0309734c7fe`.

## Blocking evidence

1. **Current suite leak can pass.** The real `Phases.execute` hashes and scans a
   clean synthetic suite log at lines 236–239. The fake after-suite process then
   appends an ObjectDB leaked warning to that file. The real analyzer reads the
   changed file at lines 327–329 and reports `strict_raw_log_failed=true`; its
   raw hash differs from the phase receipt. The wrapper ignores both facts and
   sets success from the earlier `suite['clean_log']` at lines 332–334. The
   retained `counterexample-late-suite-leak/overall.json` says `passed=true`,
   `acquisition_integrity=true`, `sample_strict_clean=true`; `analysis.json` and
   the current raw `input-mode.log` show the failure. This is a false strict
   success, not merely a missing optional receipt.
2. **Current import log drift also passes.** An independent variant appends the
   same strict warning to the import log during the later fake identity phase.
   The final raw import hash differs from its phase receipt and its current
   full text fails unchanged `native_log.failed`. No final receipt/log agreement
   check runs, so `counterexample-late-import-leak/overall.json` still passes.
   The original import gate correctly rejects a warning present at scan time;
   this counterexample tests retained evidence after that scan.
3. **Archive corruption is accepted before original deletion.** The actual
   `copy_owned_tree` runs. A fault-injected underlying `shutil.copy2` copies one
   produced private file, then changes the destination bytes while reporting
   normal completion. The final source inventory and retained archive hashes
   differ. Lines 357–359 delete the original private state and report success
   without inventorying or comparing the archive. The original and destination
   hashes are retained in `counterexample-corrupt-archive/independent-witness.json`; the
   final source inventory and changed archive bytes are retained beside it.

These are pure fault injections, not observed native events or evidence of a
historical writer, disk fault or leak cause. They test the wrapper's declared
raw-log and archive integrity gates. The controls exercise the real `acquire`,
`Phases`, scanner, analyzer, hashing, inventory and archive functions. Only Popen,
process tables, signals, clocks, Linux platform selection and the one archive-copy
fault are mocked. Real
Git handles temporary source repositories. Every engine executable is inert
file data; its command is intercepted before execution. The maintained
`synthetic_suite` helper supplies text fixture data only; assertions independently
check current hashes, scanner results, exit codes and real wrapper receipts.

## Positive boundaries and limits

`receipts.json` records the unchanged maintained suite exiting 0 with 13 tests.
The independent suite exits 1 with 14 groups: 11 pass and the three contract
counterexamples fail their required rejection assertions. `independent-initial.log`
retains the earlier 11-group run with the same three false successes. No failure
was converted to a passing expectation.

Passing independent controls cover a clean full flow; an exit-zero suite leak
that is present at phase scan; a warning after 5,000 import log lines that skips
the suite; wrong after-suite driver rejection; exact suite argv and no driver
override; actual fake-process before/after identity receipts; second-attempt
reservation refusal; real temporary-Git clean/source checks; signal-handler and
KeyboardInterrupt exceptions with cleanup and overall receipts; a 120-second
suite timeout; observed escaped-child cleanup; stubborn TERM/KILL survivors;
PID reuse refusal; and the exact 13-second reserve boundary versus a 0.001-second
available process window. These validate source control flow with synthetic
process state. They do not prove real process scheduling or cleanup.

Source inspection confirms the 4.7.2 version/executable pins, per-launch hash
checks, full tracked source/blob checks, private project custom-userdir override,
private XDG paths, actual native identity probe design, default headless Dummy
binding, generated UID retention, strict warning use and stable-identity signals.
The cleanup scope remains observed identities and original group/session. It
cannot cover an unseen escaping/reparented descendant, as the wrapper states.
File I/O and cleanup syscalls are cooperative deadline checks; source inspection
and mocked clocks establish reservation and overrun rejection, not a hard bound
against an indefinitely stalled OS syscall.

## Required next work

The largest wrapper gap is binding success to the bytes finally retained. Before
removing owned originals, revalidate all attempted phase log hashes and strict
results, require suite analysis and phase receipts to agree, inventory/compare
the produced private-state archive to the final source inventory, and retain
originals on archive failure. Freeze the corrected source and obtain a fresh
independent source review with these failing controls unchanged or explicitly
replayed against the corrected implementation.

Only after that source acceptance may root select one exact diagnostic using a
reviewed full source commit, clean complete source checkout, pinned existing
Linux 4.7.2 executable SHA-256, fresh owned output and the unchanged 120/240-second
bounds. Actual import/GDScript/API validity, engine-created UID behavior, private
native userdata, owner census, raw strict result and cleanup still require their
own observed acquisition and independent output review. No source/pure result
qualifies audible output, physical hardware, server drain or a leak fix.

No Godot/import/UID generation/GDScript compile/native/CI/OCR/service or nested
agents ran. Synthetic UID strings were written as fixture data. No product,
canonical mission or other contributor files were edited. Existing ARM and bot
strict failures remain failed; matching leak classes establish no common cause.
