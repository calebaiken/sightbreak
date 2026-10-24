# Auditor setup record

The fresh preregistration is `4dbce79d87391789c24376e895cd77c22a8b1d09`.
Changed code and test outputs were first inspected after that commit. The initial
instruction reads, Git metadata reads and own sparse-worktree initialization did
not explicitly set CPU affinity. Every Python test, source/original-byte audit,
depth-one acquisition and recorded identity check ran on CPU 4. There was no
engine, native, version, import, export, render, service or CI invocation.

One source inspection ended with exit 2 because it requested nonexistent
`scripts/test_linux_profile_fixture.py`. The stderr was:

```text
sed: can't read scripts/test_linux_profile_fixture.py: No such file or directory
```

`rg --files` identified the actual fixture/controller suite as
`scripts/test_linux_profile_overhead.py`. All 22 methods in that suite ran and
passed, alongside all 38 acquisition and nine readback methods. This was an
inspection-path error, not a skipped or passing test.

The depth-one view was initialized from scratch at
`/workspace/reviews/linux-native-fingerprint-types-depth-one`. Before fetching,
its object alternate was explicitly set to `/workspace/sightbreak/.git/objects`.
A full-SHA local-file fetch with `--depth=1 --no-tags` installed the genuine
shallow boundary at exact `8da2add4`. The view has one reachable commit, zero
local loose/packed objects and a candidate tree exactly equal to the reviewed
source. Shared objects also expose the rejected base object; ancestor-object
absence and independent network transfer are not claimed.

The initial test run attached two untracked harness directories to the clean
shallow view. All 69 maintained, ten unchanged original and seven fresh methods
passed. After the parent clarified the preferred clean-source layout, those
directories were preserved by moving them into an external harness at
`/workspace/reviews/linux-native-fingerprint-types-depth-one-harness`. A `scripts`
symlink points to the shallow candidate's scripts. The unchanged original rig and
fresh rig were rerun there and passed; loaded module paths, exact candidate
hashes and clean source status are recorded in `depth-one-external-harness.json`.
The first outputs and first untracked-status observation remain retained.

The first final `git add` refused the unchanged original rig because its correct
relative path was outside the cone sparse definition. A subsequent diff check
made that multi-command shell's final status zero; the refusal was read and was
not treated as successful staging. The exact refusal is retained in
`initial-staging-sparse-refusal.txt`. Explicit `git add --sparse` staged the
intended review evidence and unchanged rig. This changed no candidate source.

No original raw file, archive, failed output, rejected source or original rig was
edited, deleted or replaced. The source checkout's pre-existing staged restored
originals were left alone. The independent rig in this review is an exact
8,389-byte copy from `a8cf0d0`, SHA-256
`d7cf25f9034166f2fedf5299706306541acebf7703364ab26a6cf8b90344bafb`.
