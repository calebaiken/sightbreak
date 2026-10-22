# Evidence retrieval and verification

Own sparse branch/worktree starts at exact 0527715. `git show`, `git diff`,
`git ls-tree`, `git cat-file`, `rg`, `cat` and `sed` inspected committed source,
registration criteria and accepted review. Source content/validation/inventory
hashes were recomputed from Git blobs before native artifact retrieval.

Supported connected reads:

```text
github_fetch_workflow_run_jobs(calebaiken/sightbreak,39741565795)
github_fetch_workflow_run_artifacts(calebaiken/sightbreak,39741565795)
github_download_workflow_artifact(calebaiken/sightbreak,12409463411)
github_download_workflow_artifact(calebaiken/sightbreak,12409623065)
github_fetch_workflow_job_logs(calebaiken/sightbreak,119699758860)
download_file(file_00000000409c81f5909521f2c7c6c7bd)
download_file(file_00000000b15481f5a1d7f1aaba172959)
```

Both transfers succeeded within 32 MiB. The known 290,917,225-byte package was
not requested. No transfer denial or host workaround occurred. Signed download
URLs are unnecessary for provenance and are not committed. Inner receipt ZIP and
outer downloads remain in their attachment directory; raw evidence is committed
without byte changes. Original QA/receipt paths, CRCs, duplicate/symlink/traversal
checks, every indexed hash and every overlapping file were verified. The decoded
connector job log is retained at its exact 291,602 characters; patch serialization's
extra final newline was removed before evidence review. `view_image` opened all
eleven original PNGs, without local OCR.

Reproduce the read-only audit:

```sh
python docs/reports/gauntlet/m2-native-mac-ci-39741565795/independent-review/review_receipts.py
```

The initial audit's wrong weapon-name set and uncapped lethal-damage oracle are
retained as reviewer errors in `rejected-audit-assumption.json`; correcting them
preserved source terminology, health-cap behavior and tolerance. Final audit
output is in `verification.log`, with detailed `verification.json`. All source
counts refer to actual native logs; HTTP inside transaction_journal is explicitly
stubbed by the maintained source test. No native execution was simulated here.

Applied the installed `no-ai-slop` skill/eval to the report. Claims keep concrete
source/run boundaries and limits; no invented taste comparison or causal repair
was added. The full staged whitespace check reports native logs' existing spaces/
blank endings; `raw-whitespace-check.log` retains those diagnostics and raw bytes
remain unchanged. Authored Markdown/Python/JSON whitespace checks pass. No
product, canonical evidence/mission, dispatch, native API or local runtime change
is included.
