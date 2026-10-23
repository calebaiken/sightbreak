# Adapter-only source review

Exact source `b4a2cf4af787dbd811f1b59e0db8264692598b11` wins against its
unchanged default behavior for the narrow goal of making one future Windows
diagnostic selection explicit. The workflow adds one optional Boolean with
`default: false` and inserts one fixed literal argument into the original
undelayed Windows/Linux controller invocation when the runner is Windows and
the declared input is true.

This is an adapter-only source acceptance. The combined verdict remains pending
the exact independently accepted trace integration and its replay. At this
adapter commit the controller does not yet accept the flag; enabling it now
would fail argument parsing. No dispatch is authorized by this report.

The independent `check_adapter.py` proves exact recovery of all 18,248 original
workflow bytes after removing exactly the five input lines and one argument
expression. Original/reversed SHA-256 is
`5b662868c7cdc80f77ebb8c6767ff1d6b983a81870e668effabe95bd1cdde075`;
adapter SHA-256 is
`5f59b1e2eb4d1b945c0bf3958d403d3d0166ae7ce8e01a5488e29e9171b62c7a`.
The full 507-path non-document Git trees differ only at
`.github/workflows/desktop-alpha.yml`, with mode `100644` preserved. This proves
the original matrix, triggers, jobs, actions, permissions, steps, schedules,
budgets, output paths and artifacts retain every original byte.

Context inspection confirms that `inputs.observe_windows_input` is used instead
of the string-valued event payload. GitHub's declared Boolean input contract
keeps false false; a missing property is empty. The expression chooses a fixed
literal flag, so no user string enters PowerShell. Only `workflow_dispatch`
declares this input; the existing push trigger has no input. The existing
Windows/Linux step still requires successful export and excludes macOS. The
checkout action, source ref behavior and `contents: read` / `actions: read`
permissions remain byte-identical. A real dispatch still requires its own exact
source ref and release authorization.

The pure finite context model records 90 combinations of declared event, lane,
runner OS and missing/false/true input. It emits the flag only for a true manual
input on Windows. This model does not execute GitHub Actions or PowerShell and
does not validate the pending controller integration. Existing delayed legacy
and release-first commands retain their own schedules and original outputs;
the new flag occurs only once in the workflow.

Largest remaining gap: the accepted trace/controller source is not yet supplied
at a combined freeze. Native type/API compatibility, Windows observations,
input cause, delivery, route survival, cleanup and every whole release gate
remain unverified or failed as recorded before this review.

Evidence: `adapter-proof.json`, original stdout/stderr and the independent
checker in this directory. Preregistration was committed and pushed as
`07f50bfe` before implementation inspection. All shell/Python review work uses
CPU 4; no engine/native/import/export/render/CI or dispatch ran.
