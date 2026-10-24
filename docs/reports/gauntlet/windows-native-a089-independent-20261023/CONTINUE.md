# Continue the independent actual review

Current state: actual review is complete. `REPORT.md` contains the independent
FAIL verdict and separate passing scopes; `REPLAY.md` reopens the retained
originals. The monitoring handoff below is retained as historical context.

Monitoring paused at root's request on 2026-10-23 while the original remote
stock match continues. No cancellation, source edit, workflow change, retry or
final actual verdict is issued. Root will reactivate this critic after the job
completes. Provisional step scopes remain provisional.

- Own worktree: `/workspace/reviews/windows-native-a089`.
- Own branch: `codex/review-win-native-a089-20261023`, based on exact a089473.
- Report directory: `docs/reports/gauntlet/windows-native-a089-independent-20261023`.
- Original run: `39916539053`, job `120291226421`, attempt 1.
- Frozen source: `a089473481ced0f2e7b2a7468bbc5d079f92f0ff` on immutable
  `codex/v1-qualify-win-a089473`; approved combined source `04d930b`.
- Root dispatched once at 07:15:05 UTC. Independent criteria commit `69d3bde`
  followed at 07:15:41 UTC without inspecting any actual output. Correction
  `548f19a` and `REGISTRATION_TIMING.md` preserve that timing limitation.

Latest retained step read has living/settings/focus failed, plant, defuse and
full stock match successful, and development-package preservation running.
Native suites and all three input steps also report success. No actual completed-run logs, artifacts, native
receipts, OCR bytes or new PNGs have yet been retrieved or accepted.

Next, use supported GitHub tools to fetch final run jobs/steps, decoded job logs
and artifact metadata. Run metadata may be fetched read-only through `gh api`
without following log/artifact redirects. Join exact head/branch/attempt, retain
all failed/skipped steps. Download only official bounded QA and QA-receipt ZIPs
at or below 32 MiB via `github_download_workflow_artifact` then `download_file`.
Do not request the large development package, use denied redirect hosts or
substitute older output. Retain native executable/PCK claims as attestation if
its bytes are untransferred.

`safe_extract.py` checks official ZIP digests and extraction paths. Fifteen
read-only auditors were ported from the retained b2 review with source/run
constant changes recorded in `auditor-port-provenance.json`. The Windows byte
auditor additionally accounts for the new focus fixture's CRLF; actual native
hashes must confirm it. `source-expected-LF.json` recomputes exact tracked source.
`audit_focus_actual.py` independently retains reached contexts and typed rejection
without treating a correct liveness rejection as complete focus success.

Run the auditors on the new original bytes, retaining all initial reviewer-tool
failures and corrections. Inspect original PNGs directly and native OCR stdout
without launching OCR. Add precise reached/unreached focus stages, rejection
reason/raw state, original objective holds/resolution/next-buy/restarts, stock
rounds/terminal reasons/bot plants and earned disk/reopen equality. Scan every
retained native log. Compare supported scopes to original b2 run 39907358390;
hosted variability prevents causal benefit or bot-quality claims. Commit/push
official raw archives, metadata, audits, visual review, replay instructions,
hashes and final independent verdict/largest gap. Canonical root docs stay owned
by root. No local engine/native/render/OCR workload or nested agents.

Reviewer read/setup history: initial broad file reads were output-truncated and
were followed by smaller targeted reads. Two read commands stopped on absent
files: the later source-approval summary was not present at frozen a089473 and
was then read exactly through `git show 04d930b:<path>`; a guessed inherited
`verify_review.py` filename did not exist and the actual `verify_receipts.py`
was then read. Neither changed source or produced a native result. All prepared
Python auditors pass syntax compilation; no native audit has run yet.
