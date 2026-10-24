# Actual Windows verbose diagnostic verdict

**INCONCLUSIVE for reopened shutdown. Overall workflow/job FAILED.**
Run 40083894472, attempt 1, job 120842796227 at exact
7101350e5d0a2f6e4afb9a913b5b1bcf2107857a completed2026-10-24T10:19:42Z.
The living/settings producer failed before launching the reopened process.
No leaked-instance class, ID, reference count, Node path or ResourceCache row was
produced for that process. Original 40080238905 remains FAIL with three unidentified
ObjectDB leaks; this result establishes neither nonreproduction nor a fix.

## Exact request and observed scope

Pushed preregistration f44d6dd4 and admission 78e972bc precede root release 43dbc058
and the sole 09:55:49UTC request. Six admission files are byte-identical in the
release snapshot. Exact original commit/push output is retained; push stdout has
no embedded UTC and filesystem timestamps are unused. The fixed qualifier,
workflow_dispatch,7101350e and all three inputs match: lane=windows,
observe_windows_input=true, verbose_reopened_shutdown=true. The public default
workflow and original pipeline/schedules/budgets/gates remain source-bound.
No rerun, alternate qualifier or additional native lane occurred in this review.

The evaluated controller argv contains --reopened-verbose. The only offline native
command is initial client PID5124, start 0.7819999999999254seconds, final command
exit 1, without --verbose. The normal input server/client retain their original
observer user arguments and have no --verbose. Reopened engine argv is unreached;
this run never exercises the candidate's reopened --verbose branch at runtime.

Living step 30 ran 10:05:27–10:07:10 UTC and failed on
`Native route pulse sleep returned before its requested boundary`.
results.json records 102.2349999999999seconds, normal initial/reopened exits null/null
and cleanup_errors=[]. Commands record client exit 1 during failure cleanup.
The success-only descendant audit is unreached. Empty cleanup errors do not prove
normal WM_CLOSE shutdown or complete observation of every descendant.
Other reached workflow steps report success; that status is not substituted for
independent product qualification. FINAL_JOB_DETAILS.json retains every step.

## Route failure and diagnostic limit

The failed second D pulse is results.json /settings_cover_route/native_pulses/1.
Its pulse budget is 0.12567175974707734seconds; hold_until is 768.093671759747.
Recorded down API brackets are 767.968→767.968 and release brackets
768.093→768.093; finished is 768.093. The recorded API down-to-release interval
is 0.125seconds. These values do not measure physical hold or sleep duration.
The literal sleep(wait) argument, sleep entry/return, exact tested clock sample
and actual clock implementation/resolution readback are absent.

Source verify_integration_export.py:439 defaults to time.monotonic/time.sleep;
530 calls sleep(wait),531–532 enforce the unchanged boundary. Offline caller
748–757 supplies no override. Official job.log:209 identifies CPython 3.12.10.
Actions zero-based152/153 bracket the failed request;162 records failure.
The subcritic report retains exact source/JSON line anchors and all selected raw
rows. No tolerance, deadline, sleep, physical boundary or original gate is relaxed.
Root's separate source investigation may inspect this failure; this verdict admits
no correction or new execution.

Ten captures reached purchased SMG, with seven OCR stdout records, three HUD
analysis pauses and retained native reload/buy fences. Field settings/resume,
LEAVE, persisted-profile restart, reopened focus and incomplete-training checks
were unreached. These partial captures supply no complete HUD/settings/progression
acceptance. The largest gap remains the missing reopened verbose process/output.

## Source and evidence

All 508 pinned Git source identities remain bound; the game tree/content match c324.
Offline source, artifact_source and windows/source.json agree, including Boolean
false dirty flags and declared executable SHA256
1fc484bd57b292eef4281c25ae6318c72ba0e05ccb384588e16290d5088e4020.
The large native payload was not downloaded or independently rehashed.

The preregistration incorrectly predicted Windows validation bytes from the LF
checkout, yielding be2f4ea7. That literal prediction fails in the preserved first
extraction. A separate pure Git reconstruction applies Windows checkout filters
to the same pinned source and produces exact actual 225f4d95; the same method
produces exact original c324 digest 01ebd70c. Thirteen unchanged validation paths
receive CRLF conversion under unchanged attributes. This explains the prediction
error without a source/runtime change. The original preregistration, decoder
findings and failed expected comparisons remain unchanged.

Both official bounded archives pass exact GitHub size/SHA256 and ZIP CRC checks:
QA 20,899,914bytes/f0bafc376e8c6d5b614a8e6707983f6b6b99957bd0c9a6a3042542ff3fd5388d;
receipts 23,184,963bytes/dbf190f2839d20574b0c152fba39e3328b961705fca955738a336409a9a62ed5.
All 224 receipt-index entry matches its bytes/hash and QA counterpart. Both exact
archives, complete job.log and offline originals are retained. The 143,552,176byte
development artifact remains untransferred/unparsed under the32 MiB cap.

The 137 scanned native logs have zero unchanged native_log.failed() matches;
21 logs retain warnings, including OpenGL-to-ANGLE fallback. The missing reopened
log cannot be counted as a clean shutdown. Generic warnings and the narrower
native_log predicate remain distinct; original strict blockers remain in force.
No ownership chain, allocation stack, causal leak fix, performance, human/physical
result, subjective score or whole v1.0 gate is accepted.

The full staged whitespace check retains exit 2 on original Windows raw line
endings. Its complete output is retained in WHITESPACE_CHECK.json. The separate
source/report check excludes only original raw and binary archives and passes;
no native raw byte was normalized or edited.
