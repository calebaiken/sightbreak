# Independent layout OCR resource review

Accept production change `4f6147f`, frozen in clean candidate
`77836f39413577053cea5a3431a12ecd586efdbe`, for the declared child CPU reduction
and failed-attempt receipts. The candidate improves on the unchanged observer
by using 52.94% less measured Tesseract CPU on identical saved analysis bytes.
Aggregate saved-image wall time improves by only 1.53%. Native CI deadline
correction remains unverified. This review makes no visual-quality judgment.

The independent checkout is `/workspace/reviews/layout-timeout-candidate`.
Its production script SHA-256 is
`9d1ca1d2b727d5488942b1fee0470e232ce8b6b1c618e739bcb7dc9fc2f6782c`.
Static AST comparison with `7d46d2e` proves the whole production module is
unchanged after removing the new helper and its modified invocation/receipt
block. Within that block, preprocessing, PSM command, remaining-budget
calculations, return-code rejection, TSV writing and coordinate parsing remain
identical. Thus recognition requirements, FIRE/wrong-screen negatives, same-PNG
binding, two-drawn-frame fences, actions, source/ELF checks and all original
wall budgets are preserved. The helper copies the process environment, changes
only the child's `OMP_THREAD_LIMIT`, passes the original timeout to
`subprocess.run`, and re-raises exceptions after recording their type and text.

Independent recomputation reads the committed report and all 176 retained raw
TSVs, rather than trusting the comparison summary. All 22 original fixture
hashes, all analysis hashes, 88 paired TSV hashes/word lists and 88 expected
classification outcomes pass. Recorded child CPU totals are 47.861085 seconds
with inherited OpenMP and 22.521193 seconds with one child thread; wall totals
are 22.926853 and 22.577192 seconds. Maximum observed child threads are four and
one. `benchmark-recomputation.json` and its reproducer retain these calculations.

After coordinating a short CPU lane with the bot builder, the critic ran the
actual production helper through all eight maintained saved-image tests. They
pass in 14.375 seconds with the original five-second test OCR cap, including the
22 native fixtures, touch exclusion, same-frame counterexample, erased footer,
coordinate mapping and deliberately tiny real Tesseract timeout. All 46 fresh
classification TSVs are byte-identical to the candidate's retained outputs.
Original fixture bytes remain unchanged. The raw test log, results and every
TSV are retained beside this report. No native generation or rendering ran.

Additional real child-process controls set the parent's limit to eight and
observe one in the child while the parent remains eight. An unrelated sentinel
environment variable and both output streams survive. Nonzero exit seven
remains nonzero with its actual streams; an exact 0.01-second timeout and a
missing executable both propagate with failure receipts. The controls restore
the parent environment and retain elapsed time without inventing an exit code
for a killed or unstarted child. `child-policy-results.json` contains the actual
receipts and `check_ocr_child_policy.py` reproduces them.

All 23 retained evidence-index entries match their byte counts and hashes.
The separate startup audit verifies all 24 raw startup TSVs and four links from
prior native original PNG hashes to completed calls in failed CI `39719407304`.
The receipts contain 30 repeated completed matching calls after first
occurrences. Byte identity supports that limited link; it does not recover
unavailable final CI menu/settings captures or establish native timing.

The largest remaining deficiency is an exact-source four-size native rerun
under the original 12-second/remaining-confirmation OCR caps, five/eight-second
drawn-UI confirmations, 15-second menu check, 120-second case and 520-second
whole-flow limits. Independently inspect its original PNGs through the new
bounded per-size artifacts before accepting native generation or declaring the
CI timeout fixed. The prior 960×540/1920×1080 menu deadline failures and
1280×720 settings child timeout remain failures of source `0ca125d`.

The shared CPU lane was explicitly returned to the bot builder after the
independent OCR controls finished. No whole validation, visual comparison,
physical-device, other-platform or RC gate passes follow from this review.
