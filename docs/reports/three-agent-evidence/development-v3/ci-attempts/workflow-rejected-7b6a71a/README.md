# Workflow rejection, before native execution

Frozen source: `7b6a71a683ec5d1ed42d7245395c640225058e20`.
[Actions run 39879374637](https://github.com/calebaiken/sightbreak/actions/runs/39879374637)
was rejected at workflow validation: `runner.temp` is unavailable in job-level
`env` at original lines 106–108. `jobs.json` records zero jobs. No game test,
campaign, audio control, native flow or export ran; no development artifact exists
for this attempt. Raw public run API, jobs API and HTML annotation are retained.

The correction moves the three isolated audio paths into a runtime shell step,
writing `$RUNNER_TEMP`-derived values to `$GITHUB_ENV` before their first use.
No gameplay, thresholds, workload counts or acceptance gates changed.

`collect_and_lint.py` fetched the official actionlint 1.7.12 Windows archive and
verified it against that release's published SHA-256 list before execution.
`results.json` retains archive/executable hashes, actual commands and source
hashes: original workflow exit **1**, corrected workflow exit **0**. Shellcheck
and pyflakes were disabled explicitly; this proves workflow-schema/expression
validation only, not shell correctness or native execution. The corrected copy
contains the physical Windows bytes checked, not a claimed Linux execution.

The original attempt directory and downloaded executable/archive remain external
under `sightbreak-v3-evidence/ci-rejection-20261022/attempt`; binary downloads are
not redistributed here. Its failed workflow and diagnostics were not overwritten.
A new exact source commit and actual CI attempt are still required. These local
checks do not qualify a native candidate, development package or human/device gate.
