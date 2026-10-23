# Retained review-worktree setup failure

The own review worktree was created with `git worktree add --no-checkout` at
49ae54b0. Running `git sparse-checkout set --no-cone` without first initializing
the new index left it empty. Commit81344469 accidentally recorded omitted tracked
paths as deletions while adding the preregistration. This was an own-branch setup
failure, not a candidate-source failure. No root worktree or contributor source
changed. No test, native executable, CI, large clone or archive ran.

A `git read-tree --reset -u 49ae54b0` recovery emitted a preregistration-path
not-uptodate warning and restored the candidate index/source while dropping the
materialized copy of that file. The following failed `git add --sparse` found
no preregistration file. Both failures were observed; they are not passing checks.
Corrective own commitd76a4cc1 restored the entire exact49ae54b0 tree. Independent
`git diff --name-status 49ae54b0 HEAD -- . ':!docs/**'` and clean status were empty.
This report then recopied the original preregistration byte-for-byte.

Do not cherry-pick81344469 or d76a4cc1 into root. Future review evidence commits
are documentation-only children of the restored exact candidate. The original
preregistration remains in /workspace and was independently sent to root before
the candidate freeze with SHA25624fa284b1c594566860d596643ce1b41eee9133040e6778c932efed3139ffd07.
