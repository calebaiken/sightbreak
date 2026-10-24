# Original timing contract, inspected without execution

Exact source c90fedfd56a09bd0ba13cce5565ccd160891c3fb is hash-bound in
ORIGINAL_SOURCE_BINDING.json. No implementation or capability function ran.

scripts/verify_offline_export.py:200 declares timeout default300 with help
“Whole-flow wall deadline, plus separately bounded failure cleanup”. Lines231–232
set started=time.monotonic() and deadline=started+args.timeout. remaining()268–273
subtracts that same clock and fails when exhausted. Initial close884, reopened
close1060 and study_close helper249 call wait(timeout=min(20,remaining())).
Thus each20-second close allowance is INSIDE the300-second whole flow, not an
additional four times20 seconds. Four300-second flow maxima plus one5-second
cleanup reserve give1205. Preservation120 and transfer60 give1385 reserved seconds;
a30-minute1800-second job leaves415 seconds for setup only when the budget anchor
really covers all preceding job work.

scripts/windows_shutdown_study.py:149 passes --timeout300 and trial metadata208
records flow300/close20. The inherited driver's finally cleanup1116/1123 contains
per-process waits; those local waits do not themselves prove a single aggregate
5-second collection cleanup. Future source/admission review must show that the
outer collection policy clips all nested cleanup without creating another budget.
This is a prerequisite, not an observation that the revised study already enforces it.

Read-only discovery first guessed scripts/shutdown_study* in root; that glob was
absent. Root supplied the exact c90 source paths above, which were then read by
Git object. No source, old output or runtime state was changed.
