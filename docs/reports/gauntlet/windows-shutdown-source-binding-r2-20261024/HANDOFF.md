# Physical source identity correction: bounded source handoff

Frozen sourceb6da3aecfc2d88443c5e0757a9bd9320122a1d4d, branch
codex/windows-shutdown-source-binding-r2-20261024, own worktree
/workspace/sightbreak-windows-shutdown-source-binding-r2. Preregc7ae426c precedes
implementation; originalc90/239 and independent reject75ddeb26 remain unchanged.
Existing study critic is reused for this component only; no fresh thread or
builder approval. No native acquisition, helper trial, version probe or CI action.

source_binding now reads every required physical non-doc source and compares it
with its exact frozen Git blob, independent of assume-unchanged/skip-worktree/
working attributes. Missing, symlinked, changed or unsupported source rejects;
POSIX owner-executable mode and same-read identity/size/mtime/mode stability are
checked. Git tree parsing is NUL-delimited for spaces/Unicode. Every required
source must be materialized. On Windows only, exact LF-to-CRLF conversion of
strict UTF8/noNUL/noexistingCR text is recorded separately; no arbitrary filters
or general normalization run. Windows executable bits are explicitly unmeasured,
with canonical Git mode retained. These are observed file comparisons, not a
claim of atomic whole-filesystem or already-loaded-bytecode attestation.

Pure-r1 passes36 methods (8 new physical controls+28 existing), no skips/errors,
0.67223755s outer subprocess/CPU4. New source tests use exclusive temporary Git
repositories, never engine/native processes. They show hidden model AND nonmodel
mutations under both index flags cannot inherit identity; missing/symlink/mode/
read-race/invalidlineconversion cases reject. Clean Unicode paths and explicit
Windows line endings bind. Existing protocol/driver/game behavior stays unchanged.
The initial source commit964a omitted the new test after sparse-path refusal;
SOURCE_FREEZE_NOTE preserves that setup failure. Additive b6da includes it; no
history rewrite or preflight from the incomplete test commit occurred.

Exact cleanb6da real preflight exits2/BLOCKED with513 physical source receipts,
execution_authorized=false. Full stdout/stderr/JSON retained; stderr0. This is
source-only reading/Git metadata, no WindowsOwner/driver/engine. No performance
cost or actual Windows checkout behavior is measured. Full513 non-doc physical
blob/mode proof changes one original source and adds one test;511 original paths
remain exact, including game/defaultdriver/workflow/oldtests/receiptreader.

This closes only the builder's proposed fix for one independent rejection group.
Whole study remains REJECTED/BLOCKED pending independent review and separate
receipt-completeness correction. A passed=true-only result can still falsely
pass the old pure trial_evidence seam; no full-study readiness is claimed.
Complete four-trial retention still has no finite proof under two32MiB limits,
including wrapper overhead. No public ADMITTED route or execution authorization
is added. Source freeze/handoff acceptance cannot release a native study.
