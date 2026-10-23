# Independent Linux lane review

Code approved for `b536542` + `807b56b` against immediate pre-lane `67a5f54`.
The workflow and evaluator remain unchanged through `738a381`. This review ran
no Godot, OCR, native gameplay or remote workflow.

Parsed YAML has exactly two changed paths: manual lane options and the matrix
include scalar. Adding `linux` preserves the prior options. Restoring only those
two exact prior values reproduces the entire baseline workflow. All 38 steps,
the public-repository job guard, permissions, deadlines, source fences, artifact
settings and per-size original PNG preservation are identical. The original
Linux layout step still invokes the unchanged default budgets.

`replay.py` independently tokenizes the actual scalar and applies expression
precedence (`==`, `&&`, `||`) and case-insensitive string comparison. All 15 cases
pass: the original ten cases plus an empty input, uppercase Linux/Windows/ARM
inputs and another event. Default, push, explicit all and unknown inputs select
the original four hosts. Windows and ARM keep their original single hosts.
Only explicit manual Linux selects Ubuntu 24.04 alone.

The corrected evaluator also passes its ten cases against `67a5f54`; its replay
matches the committed receipt exactly. Evaluating the dynamic baseline and
restoring its exact scalar fixes the earlier list-versus-expression mismatch
without relaxing the unrelated-field comparison.

The first replay remains rejected. Running the actual `b536542` evaluator
against `90740e0` again exits 1 with no stdout and the unrelated-field assertion.
That older baseline lacks the five per-size PNG packaging/upload steps.
Restoring the older input and matrix values still leaves the steps unequal.
The original retained rejection is `../rejected-baseline.txt`; the reproduction
is `original-rejection-reproduced.txt`.

Reproduce the independent check from the repository root:

```sh
python3 docs/reports/gauntlet/native-layout-timeout/linux-lane/independent-critic/replay.py
python3 docs/reports/gauntlet/m2-ios-compile/arm-lane/evaluate_matrix.py --baseline-ref 67a5f54
```

The remaining selector gate is the actual returned run SHA and exactly one Linux
job. Then inspect all original Linux startup, regression, input, journey,
objective, full-match/restart and layout gates with unchanged deadlines. Code
approval establishes no native timing, Windows/macOS acceptance, physical
performance or aesthetic result.
