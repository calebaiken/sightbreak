# Intel experiment dispatch

The standalone manual workflow was added at `b9826d4` on
`codex/v1-mission-playability`. Actual dispatch command:

```sh
gh workflow run macos-render-diagnostic.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability
```

GitHub returned exit 1, `HTTP 404: Not Found`, for
`/repos/calebaiken/sightbreak/actions/workflows/macos-render-diagnostic.yml`.
No job ran. The new workflow is not registered on the default branch. No shared
branch merge is authorized or performed to make it discoverable.

The existing registered `desktop-alpha.yml` now invokes the same reviewed runner
only on `macos-15-intel`, after the unchanged shipping startup qualification and
existing minimal/frozen/candidate diagnosis. Its default driver and 120-second
per-case bounds remain unchanged. This adds up to ten minutes to the Intel job,
inside its existing 60-minute cap. Diagnostic outcomes cannot turn a failed
shipping gate into a pass.

Output is nested under `macos-diagnostics/render-features`, so the existing full
artifact preserves all files and the bounded receipts packer includes JSON, logs
and native sample text. Original PNGs remain in full QA evidence. The dedicated
workflow also remains available for future default-branch registration through
the normal reviewed merge path. Actual dispatch/run identity and native findings
must be recorded separately after execution; this file does not claim a run.
