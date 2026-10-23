The first source-audit run failed because this new sparse checkout omitted
`.github/workflows/desktop-alpha.yml`, one of the unchanged non-document paths
that the audit reads. Its empty JSON and exact traceback remain retained as
`initial-source-audit-sparse-omission.*`. Restoring the exact tracked `.github`
directory made the same audit pass. No check or source invariant was removed.

The focused acquisition tests also need the tracked report fixtures in
`correction-r1`, `correction-r2` and `packed-remap-boundary-r1`. Those paths were
included before their first invocation. No engine process ran.
