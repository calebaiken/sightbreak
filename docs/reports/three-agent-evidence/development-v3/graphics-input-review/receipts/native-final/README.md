# Separate native automated test evidence

This directory is intentionally **not part of the blinded visual packet**. Do not give it to the independent visual critic before the critic freezes its judgement.

The native `reload_continuity_test.gd` is run without source changes or threshold changes, using the exact requested reconciliation source, native Windows OpenGL compatibility rendering, actual 1280×720 frames, fixed simulation time, and Dummy audio.

The full default sunlit-normal attempt (`reload-continuity/`) reached the 600-second bound without a completion marker: **inconclusive**. The original runner then stopped while printing to stdout closed by the OpenCode server restart. Originally planned optional calm/shade native-oracle configurations did not start; all three matched visual-capture configurations did complete independently.

`reload-continuity-focused-56-110*/` is a separate supported `--from=56 --to=110` sunlit-normal attempt. The unchanged source's header specifies at least ticks 56..110 for its checks. A focused result does not replace the retained full-range timeout and must not be presented as a full-range pass.

**Final status: inconclusive.** The focused attempt reported native allocation errors in `_frame` during image readback and exited with `3221225477` (`0xC0000005`). Like the full-range timeout, it produced neither a completion marker nor a completed per-tick CSV. No oracle pass/fail verdict exists. See `FINAL-STATUS.json`. No further native retries were made, and no test/source/threshold changes were made.

Each attempt retains its per-tick CSV if completed, engine log, command, process return code, and any error/timeout log. Its optional lit/identification PNG export is disabled to reduce native image-readback memory pressure; the native identification pass and pixel checks are unchanged. A native process has a 600-second time limit; on timeout only that process tree is terminated. `outcomes.json` records completion markers and hashes without transforming them into visual scores or performance claims.

This is the source's existing automated oracle, not an independent aesthetic judgement or proof of player-perceived motion quality. Native test results must remain separate from the source-independent blinded comparison.
