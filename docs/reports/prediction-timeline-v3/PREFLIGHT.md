# Preflight retention

The files in `preflight/` are copied from the worker's original external output
directory, not recomputed final results.

- `candidate-import.log`: unsuccessful official Godot 4.7.2 import (out of memory,
  process exit 3221225501 / `0xC000001D`).
- `candidate-import-retry.log`: successful serial import using
  `--single-threaded-scene` after the first failure.
- `timeline-first.log` / `timeline-first.json`: exploratory probe before
  `d5bdd538bb13e3cc97f4eae577c36d3d050a2a3e` was frozen. The working fixture was
  uncommitted, with fewer diagnostic counters/assertions. This is not part of the
  final matched comparison or its source-bound pass count.
- `source-audit.json`: exact Git-blob hashes for the key movement/authority/privacy
  files, an empty runtime diff and selected historical V2 campaign metrics. The
  historical campaign's SHA256 is recorded; prediction-disabled error is null in
  this derived summary because it is not prediction accuracy.

Separately, the initial command

```text
git worktree add --detach C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-prediction-baseline701 701ce2c
```

failed during checkout. The original tool response (not captured to a raw file)
reported:

```text
error: Out of memory, malloc failed (tried to allocate 590175 bytes)
fatal: packed object 63bfe02be2b97b685f596a2ad237dd3e25ca3905 (stored in C:/Users/blith/OneDrive/Documents/Default Project/sightbreak/.git/objects/pack/pack-33e783dd28637e1f35cc54efa4e4c214b988827a.pack) is corrupt
```

The concurrent Godot log proves an allocation failure too. Subsequent exact-source
Git blob reads succeeded. No `git fsck` was performed and no claim of a general
repository integrity check is made. The failed worktree did not remain in
`git worktree list`; no source-owner worktree was removed. All final native runs
use fresh game-only archives instead.
