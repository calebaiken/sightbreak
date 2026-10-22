# Independent source review: REJECT

Exact source: `4df02e9d04c6e9b09bcb7f180c3223abda229da4`. This combined source contains the corrected screen bounds and the first separate verbose diagnostic.

The screen component passes 27 packaged controls and 146 independent synthetic cases. Its geometry correction closes all eight original float-edge cases.

Reject the combined commit under its diagnostic criteria. Missing any of `results.json`, `isolation.json`, or `input_mode.log` produces FAILED/exit 1 before selection instead of the specified honest skip for absent original failure evidence. All three independent missing-file cases launch zero mocked processes, so this is a status/selection defect, not an unsafe native launch. Independent finalization and receipt-check overrun cases also show a clean repeat can be reported after the 240 s budget. The expanded independent diagnostic suite records five failing subcases and retains complete output in `independent-diagnostic-4df02e9.log` and JSON in `independent-diagnostic-4df02e9-results.json`.

Other independent pure lifecycle controls pass: the actual inherited private-project harness, produced-file hashes, clean and warning repeats, import/probe warning rejection, owned process cleanup, timeout, source mutation, and original evidence mutation. All processes are mocks; only synthetic files in temporary directories are created.

The builder corrected missing-proof selection and post-finalization deadlines in a866c73. This report preserves the rejected combined iteration. Run 39732825169 and its original strict input_mode failure remain unchanged.
