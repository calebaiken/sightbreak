# Independent R2 source decision: ACCEPT

Accepted source-only scope: exact
`d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53`.
Own preregistration `0165f0c8` preceded R2 implementation inspection and checks.
Handoff base is `5cf2085529bdd0859a81e66248a974175fc5630f`.
This decision approves the corrected source contract for the separate read-only
diagnostic. It grants no native, Apple compile, engine/import, OCR or CI release.

The three previously reproduced source blockers are corrected. The original
six independent boundary methods pass unchanged against my fresh exact-source
depth-one checkout. All twelve maintained commands pass, 118 top-level methods;
eight additional independent methods also pass. No candidate test failed in
this R2 review. A report-audit setup error is retained below.

## Corrected behavior and independent evidence

1. `NativeAX.call()` measures actual native start and return. Results at or
   beyond 0.25 seconds reject while the original five-second deadline stays
   fixed. The extra independent controls test success and native-error returns
   at 0, 0.249, 0.250 and 0.300 seconds; only returns below the cap pass the
   boundary. This verifies rejection after return, not interruption of a call
   in progress. Existing whole-deadline and window guards remain in place.
2. Create/Copy +1 results enter the ownership registry in `finally` before
   post-call guards can reject. Full-registry and failed-registry paths release
   acquired references; borrowed entries are retained before ownership.
   Original three leak reproductions now pass. Additional controls cover an
   out-parameter written before a `BaseException`, pre-call window rejection,
   full-registry rejection concurrent with a late return, idempotent close,
   and a borrowed array child retained before a foreign-PID rejection. The
   resulting release lists match exactly-once ownership. The maintained tests
   also cover native error, wrong collection type/count, NULL child, decoding,
   CFString-key and registry failure paths.
3. Counted UTF-16 units are checked against decoding of the entire bounded
   UTF-8 conversion buffer. Interior NULs remain visible for control rejection;
   trailing NUL loss cannot pass the original unit count. The original false
   Deploy-title reproduction now rejects. Independent controls preserve exact
   non-ASCII, non-BMP and combining text; check 64-byte role boundaries and
   512-byte titles; and reject malformed UTF-8/surrogates, incorrect UTF-16
   counts, leading/interior/trailing NUL, C0/C1 controls and a full nonterminated
   buffer. Complete valid native labels still pass the full shared traversal
   and validator while their original OCR row remains confidence 0.5 and
   `gameplay_target_accepted` remains false.

The extra controls are in [review_r2_boundaries.py](review_r2_boundaries.py) with
raw output in [independent-r2-boundaries.log](independent-r2-boundaries.log).
They construct fake C endpoints around actual adapter methods; no native library
or executable is constructed. [exact-source-pure.log](exact-source-pure.log)
retains the unchanged original six-method replay and all twelve maintained
commands, output, exits and durations. Source acceptance does not rest only on
the builder's test counts or on a replacement model of the native reader.

## Exact source, preserved failure and execution bounds

[depth-one-setup.log](depth-one-setup.log) records a new sparse direct fetch of
the exact freeze, shallow=true, exactly one reachable commit and clean status.
Only scripts, workflow, screen-identity fixtures and the original derived-OCR
receipt subtree were selected. No historical commit is required by maintained
controls. [source-preservation-and-depth-one.json](source-preservation-and-depth-one.json)
binds the tested files to frozen Git blobs and confirms the final clean checkout.

The source delta from rejected `cf4de47f` is exactly the observer, title contract
and maintained structural/source test file. The controller, AppKit adapter and
workflow are byte-identical. All eight preserved original helper/runtime files
match their fixtures and rejected-source bytes. Both game trees remain
`55691684d31d44f1680141954bbe530443de9d1f`; audio, protocol, authority and economy
are unchanged. The original per-stage/whole budgets, own-PID/unique-window and
geometry binding, privacy pruning, zero-event/action/setter/prompt restrictions,
single focus, raw native PNG/Vision evidence and ordinary 0.8 OCR selector remain
the same. The admitted diagnostic-only launch option and honest private-menu
profile-write inventory amendment are unchanged.

The original source `cf4de47f` remains REJECTED under `12ec93dd`. Its report,
unchanged replay script and five-failure raw log match their original Git blobs,
the R2 retained copies and their index hashes. The original critic worktree
remains clean at `12ec93dd`. No old failed assertion or verdict was rewritten.
The c838907 / run 39920948579 gameplay result remains FAILED: native and fixed
2× Deploy confidence 0.5 versus required 0.8 before any CGEvent.

Root's phase clearance is retained in [PHASE_CLEARANCE.txt](PHASE_CLEARANCE.txt)
and the command receipts. Every new shell verification command and its child
processes were pinned to CPU 4; recorded affinity is `[4]`. No native, Apple
compile, engine/import, capture/OCR executable, service, CI, nested agent or large
archive ran. The native/profiling lane was not released for this review.

The largest remaining gap is actual exported behavior: this source review does
not observe the exported AX tree, new observer TCC trust, Apple ABI/string
behavior, native geometry agreement or completion within fixed budgets. A
separately released diagnostic attempt and independent actual-output review
remain necessary. No ordinary gameplay or broader platform gate passes here.

## Retained review setup error

The first preservation-audit script assumed the R2 retained-copy directory also
contained the old preregistration and all earlier receipts. The actual checked-in
index intentionally lists only the review, unchanged control script and original
failure log. That mistaken lookup produced this raw error before an audit result
was written:

```text
FileNotFoundError: [Errno 2] No such file or directory: '/workspace/reviews/m2-mac-ax-r2-fresh-source-critic/docs/reports/gauntlet/m2-mac-ax-read-only/r2/rejected-independent-review/PREREGISTRATION.md'
```

The corrected audit used the actual checked-in index, compared every indexed
file against its original Git blob and retained the successful JSON receipt.
No implementation, fixture, test expectation or old failure evidence changed.
