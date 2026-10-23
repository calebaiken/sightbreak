# Executor recovery, 23 October 2026

The executor is running again, with an older workspace snapshot. The contributor
checkout `/workspace/sightbreak` remains clean on `work` at `4d8cdb33`.
Published mission and checkpoint history were fetched into a new isolated sparse
checkout, `/workspace/sightbreak-v1-recovered`, branch
`codex/v1-executor-recovery-20261023`, based on `917b143b`.

A separate read-only inventory agent checked the common Git objects, refs,
reflogs, worktree metadata, relevant workspace text and attachment/archive
metadata. Before fetching, none of the nine requested unpublished commits was
present among 3,609 common objects. After fetching, root still cannot resolve
`da46730b`. This means not found in the checked snapshot and sources. It does
not establish permanent deletion. No previous unpublished raw output is claimed
as recovered. The published checkpoint preserves its historical record.

Godot 4.7.2 binary SHA-256 is
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
The inventory verifies the binary and six installed template files against the
locally checksum-validated upstream archives. No engine or service ran during
inventory. Available space was 32,034,476,032 bytes.

## Accepted market guard integration

The documented PR29 builder set and three independent report commits were
cherry-picked after checkpoint PR30, excluding its obsolete NEXT-only pair.
New integration tip `7795632` has identical oracle, runner and refresh-test bytes
to independently reviewed source `985a9d71`. Original review and both CI logs
are retained in `../m3-market-refresh-guard/independent-critic/`.

The restored local test invocation first failed before launch because its output
directory was relative to scripts. The next invocation ran all 37 tests, with
one missing-archive fixture error caused by a sparse path added from scripts.
Its complete failed log is retained. Restoring the exact tracked archive from
the repository root permits all 37 tests to pass in 0.114 seconds, zero skips.
Neither failure was skipped or converted to a passing result. No native client,
API or database was started. The old market archive is unchanged.

## Next product work

A builder is reconstructing a new bot dry-weapon benchmark from recoverable
source. A separate builder is preparing an actual macOS ordinary-play journey.
Both require fresh source critics and source-bound native outputs before
acceptance. Missing historical touch-contrast and cleanup work remains pending;
its old pixel results cannot qualify a newly reconstructed candidate.
The release gates remain open.

## Dependency refresh

Actual open-PR query confirms main `4d8cdb33`, mission PR27 `ad6cdc20`,
checkpoint PR30 `917b143b`, market guard PR29 `b696ca93`, map PR26 `778c89a6`
and actor-order PR28 `2641ddf8`. V3 PR17–21 remain siblings on PR16. PR17
still reports two failed checks and one passing audio check. PR1 and art PR2
have newer heads than the restored contributor snapshot; neither is integrated.
The full query result is retained in open-prs.json.
