# Review commands and bounded failures

Read-only source review used `rg`, `sed`, `cat`, exact `git show`, `git diff`,
`git ls-tree` and `git cat-file` in the own sparse worktree. Source identities
were calculated from committed blobs, rather than the deliberately omitted game
working-tree directory. An initial validation-hash calculation sorted all roots
together; the maintained order is scripts → .github → game/tests. The rejected
hash and correction are retained in `source-verification.json`. The corrected
value was committed before native artifact receipt and matches all native source
records. Early filename guesses `macos_input_mode_leak_diagnostic.py`,
`native_scene_suites.py`, `verify_native_scene_suites.py` returned missing-file
errors; actual maintained filenames were then inspected. Ordinary `git add`
initially refused the new review directory outside the sparse cone; `git add
--sparse` staged only owned review paths. No product action resulted from either
source-read/staging failure.

Supported connected GitHub reads:

```text
github_fetch_workflow_run_jobs(calebaiken/sightbreak,39739927334)
github_fetch_workflow_run_artifacts(calebaiken/sightbreak,39739927334)
github_download_workflow_artifact(calebaiken/sightbreak,12408952206)
github_download_workflow_artifact(calebaiken/sightbreak,12409116554)
github_fetch_workflow_job_logs(calebaiken/sightbreak,119694416545)
download_file(file_0000000006f481f5b37322e352c15080)
download_file(file_00000000d9dc81f59c515f8c54e85704)
```

Both downloads succeeded under 32 MiB. Archive extraction rejected unsafe paths,
duplicates and symlink entries before writing only owned evidence files. All
receipt hashes and overlaps were verified before reading result fields. No
transfer failure or host denial occurred. The known 290,795,763-byte full package
was not requested because it exceeds the transfer cap. Temporary signed URLs
are unnecessary for provenance and are not committed. `view_image` opened all
eleven original downloaded PNGs; no local OCR engine was run.

Reproduce the read-only retained receipt audit:

```sh
python docs/reports/gauntlet/m2-native-mac-ci-39739927334/independent-review/review_receipts.py
```

The audit verifies every indexed hash, all actual suite logs/producer paths and
copied userdata inventories, exact source and menu image hashes, event/focus
sequence, recorded cleanup, honest repeat absence, iOS source/PCK/linker evidence
and startup trial logs/hashes. It launches no engine, native API or subprocess.
`verification.log` retains its successful output. Native test counts refer only
to the original runner logs, not the Python audit or mocked source controls.

Applied the installed `no-ai-slop` skill and its `eval.md` to the final report:
claims retain sources and limits,
no fabricated comparison or cause is added, and the report ends on the next
evidence boundary. This is newly authored review documentation rather than an
edit of user prose, so a separate “What changed” editing section does not apply.

The full staged whitespace check flags native logs' original trailing spaces and
blank final lines. Its output is retained in `raw-whitespace-check.log`; those
bytes are preserved. The separate check of authored Markdown/Python/JSON passes.
One documentation patch with an incorrect context line was refused before any
edit; the corrected patch succeeded. No native evidence was modified.

An attempt to pass the full decoded job log through a shell argument was refused
with “Argument list too long” before process creation. The initial patch-based
serialization had added one final newline; it was corrected to the connector's
291,558-character decoded log. Original ZIP receipt bytes were unchanged.
