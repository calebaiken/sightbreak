# Separate manual ARM lane review

Candidate: `33d6aa56d2e203ce624e3c331c8ea36f5ff16fca`; comparison: `90740e0`.
Reviewed independently on 2026-10-22 after the SDK correction review.

Verdict: accept the separate workflow change for the next native attempt. It
adds a manual host choice and leaves every selected-host gate in place.

The actual YAML contains two changes: a `workflow_dispatch` choice input named
`lane`, defaulting to `all`, and an expression for `matrix.include`. A choice
input supplies a string. The expression selects its one-host JSON only when the
event is `workflow_dispatch` and that string is `arm-macos-ios`. Both JSON
alternatives are nonempty strings, so the `&&`/`||` selection returns the intended
JSON. `fromJSON` produces the array of objects expected by `matrix.include`.
The input does not enter a shell command. Missing, empty and unknown input
values fall back to the original four-host matrix.

The reviewer parsed both exact commit versions with PyYAML BaseLoader and
independently evaluated seven cases: missing, empty, `all`, ARM and unknown
dispatch input; ordinary push; and push with an ARM input value. Only explicit
manual ARM selected `[{"os":"macos-15","target":"macos"}]`. Restoring the two
changed YAML fields made the entire parsed candidate equal the baseline.
Results and workflow hash: [workflow-independent.json](workflow-independent.json).
The builder's separate six-case evaluator was also rerun at exact clean source
`33d6aa5`: [workflow-builder-evaluator.json](workflow-builder-evaluator.json).

The selected ARM host still runs all existing source regressions, native package
checks, graphical diagnostics, unsigned iOS qualification and artifact steps.
The 60-minute job timeout, 17-minute iOS step timeout and 900-second shared
qualification budget are unchanged, as are permissions and the pinned actions.
Default dispatch, explicit `all`, and push preserve the original matrix order
and four host/target pairs. This lane provides no new Windows, Linux or Intel
Mac qualification.

The largest remaining uncertainty is GitHub accepting the new input from the
selected branch reference and creating the expected one-host run. The reviewer
did not dispatch. The existing workflow is registered, but static YAML and a
local expression replay cannot establish the remote dispatch result. Inspect
the returned run's head SHA, event and jobs before treating it as the intended
native attempt. If GitHub rejects the new input, retain that response and use
the already registered workflow's full default matrix without weakening gates.

No Actionlint or GitHub expression engine was available locally. `/usr/bin/go`
does not provide the Go language toolchain, so the attempted Actionlint install
could not run. The official GitHub contexts page was blocked by the network
proxy with HTTP 403. The review therefore relies on source inspection, parsed
YAML identity and the documented expression/input behavior; actual dispatch
compatibility remains unverified until the next run.
