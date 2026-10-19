# Attempt chronology

1. `preflight-baseline-1/`: frozen `701ce2c` runtime, then-uncommitted external
   fixture. The shot observer lambda expected four arguments, but the actual
   `SBActor.shot_fired` signal supplies three. Both native peers exited zero but
   the server logged that fixture error twice. The driver rejected the run.
   The measured stale movement is diagnostic only; this is not a passing baseline
   acceptance run. The first Windows editor import also marked tracked `.import`
   metadata modified, so source-before/after cleanliness differed.
2. `preflight-candidate-1/`: corrected three-argument observer and uncommitted
   six-line runtime candidate. Snapshot-gap stop/recovery and hostile-replay idle
   expiry passed their provisional metrics, with clean native logs. The driver
   still exited one because source identity changed during preparation/import.
   It is preflight evidence, not the frozen matched result.
3. Preparation restored only generated tracked `game/assets/**/*.import` metadata
   in the two owned worktrees, retaining native import/class caches. Runtime was
   committed as `f3ceaad`, fixture/driver as `997e0b6`. Measured source trees are
   then checked clean before/after. The frozen run uses `--skip-import`; a fresh
   reproduction must import once before freezing and measuring its source.
4. `baseline-r1/` and `candidate-r1/`: sequential same-host measurements using
   the identical frozen external driver/probe, with raw process logs, commands,
   authority/client rows, metrics and source identity in each summary.
   `matched-run-receipt.json` records the outer controller commands/exits/durations.
   Both source trees remained clean and both nine-group regression sets passed.
   Candidate: 16/16 pairs passed. Baseline: 15/16 clean pairs; the first off-mode
   stale-replay client logged a shared-start JSON parse/nil-access error before
   measurement. The baseline driver exited one rather than hide that error.
   All four baseline snapshot-gap runs show ~1.003 m stale authority travel; all
   four baseline stale-replay runs retain the actor through second 34, but the
   error-bearing pair is not counted as clean acceptance evidence.
5. `barrier-control-preflight/`: fixture-only defensive parsing plus deliberately
   empty barrier exposed `PermissionError: [WinError 5] Access is denied` from
   `os.replace(start.tmp, start.json)` while native readers held the destination.
   The outer command's traceback was displayed in the session; native logs,
   partial summary and barrier files remain here. Both children were terminated
   by the driver's error cleanup. No gameplay result is claimed.
6. `barrier-control-preflight-2/`: bounded rename retry plus guarded native parse
   handles the same injected empty barrier. One native steady pair passes, both
   readers report retries, and no native script/resource error is logged.
   This remains an explicitly dirty preflight. The corrected fixture/driver was
   then frozen as `77f2040`; runtime bytes remain those of `f3ceaad`.
7. `baseline-r2/` and `candidate-r2/`: complete fresh matched run with the same
   empty-barrier control on both peers before every measurement. The final source
   IDs, complete outcomes and commands are recorded in the r2 summaries and
   `matched-run-r2-receipt.json`. Earlier attempts are not relabeled.
   Candidate completed 16/16 native pairs plus all nine groups, clean. Baseline
   passed its nine groups, then its first client crashed before admission with
   `alloc_static` / `_alloc_exact` null-memory errors and signal 11. Its full native
   crash log is retained under `1-steady-prediction-off/client.log`; no baseline
   measurement completed in r2. A later host sample showed about 0.042 GiB available
   physical memory and 0.767 GiB available commit. This is an allocation/startup
   failure, not evidence of gameplay divergence.
8. `baseline-r3/`: only the missing baseline workload is repeated, with the exact
   same frozen `77f2040` harness, inputs and gates. The successful `candidate-r2`
   is retained. The outer controller additionally records host memory every
   0.5 seconds; it does not alter the native command or measured code. Its full
   command/exit/duration is in `baseline-r3-receipt.json`.
   All 16 native pairs and nine maintained groups completed with clean logs/source.
   All eight baseline stale-input improvement gates failed as expected, while
   the eight positive controls passed. The final raw-timeline verifier passed;
   two supplemental welcome/alias groups also passed on both frozen sources.

The server restart occurred before the runtime commit completed. Git status and
history were checked afterward; no completed frozen measurement was discarded
or restarted. Earlier preflight directories remain unchanged.
