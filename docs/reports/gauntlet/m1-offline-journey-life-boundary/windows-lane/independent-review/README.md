# Independent Windows lane review

Reviewed on 2026-10-22. Candidate: `47b142d654ad8b73b4700ca5b7427b25ab7682b8`.
Comparison: `7d46d2eb9c2c690fe0364eb6fc64f1bd85b5d226`. The reviewer used an
isolated worktree, reused the installed quality skills, and changed review
evidence only.

Verdict: accept the workflow change for the next Windows attempt. No blocking
finding. The candidate is preferable for this retry because it selects the
needed Windows host while preserving all existing gates on that host. This
approval establishes neither a native Windows outcome nor another platform pass.

The exact workflow diff adds `windows` to the existing manual choice and places
its explicit manual selection before the existing ARM clause. Choice inputs
supply strings. `&&` binds before `||`, and each selected JSON string is nonempty
and truthy. Therefore a manual `windows` input selects one Windows host; a manual
`arm-macos-ios` input still selects its existing ARM host; all other supported
events and choices fall through to the previous selection. `fromJSON` returns
the array of objects expected by `matrix.include`. The input does not enter a
shell command.

The reviewer independently parsed both exact commit versions with PyYAML
BaseLoader, restored only the prior lane input and matrix scalar, and required
the whole remaining workflow to match. All 33 steps, job conditions, permissions,
timeouts, pinned actions, artifact paths and other fields are identical. The raw
diff also contains only the two workflow lines described above. The Windows
native observer correction was reviewed separately and is outside this verdict.

[Independent controls](independent-check.py) evaluate the actual old and new
scalars through a separate Node runtime for their standard logical operators and
JSON parsing. Eighteen cases cover manual dispatch, push and workflow_call with
missing, empty, `all`, ARM, Windows and unknown inputs. Every result matches the
previous matrix except explicit manual Windows, which changes from four hosts
to `windows-latest`/`windows`. The ARM result is identical in both expressions.
Results, exact refs and workflow hashes are in
[independent-result.json](independent-result.json).

The extended repository evaluator also passes its eight cases at exact source
`47b142d`: [builder-evaluator.json](builder-evaluator.json). That evaluator compares
against the original four-host matrix at `90740e0`; the independent control
above separately compares this delta directly against the requested `7d46d2e`.
Both require equality of all unrelated workflow fields.

Reproduce from a checkout containing these commits:

```sh
python3 docs/reports/gauntlet/m1-offline-journey-life-boundary/windows-lane/independent-review/independent-check.py "$PWD"
python3 docs/reports/gauntlet/m2-ios-compile/arm-lane/evaluate_matrix.py --baseline-ref 90740e0
```

These are static controls, not execution of GitHub's expression engine. The
largest remaining gap is the actual frozen-source Windows run. After dispatch,
verify the returned head SHA, manual event and exactly one Windows job, then
inspect its native journey and every selected-host gate before claiming a pass.
No dispatch or native execution was performed by this reviewer.
