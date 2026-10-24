# Retained initial sparse materialization failure

The new reviewer worktree was created with --no-checkout at exact frozen
4cf6ac8e744603ed6af122a362036d276754cc76. Its index was initialized with
read-tree HEAD before sparse configuration. Selected tracked files nevertheless
remained absent: cat AGENTS.md failed with No such file or directory, and the
initial preregistration git add/commit attempt did not commit anything. The
unchanged full short status is retained in setup-initial-status.txt.

No candidate code was inspected and no test ran. This is a retained checkout
setup failure. Explicit restore is limited to this newly created own worktree;
no other checkout, raw output or branch is reset or edited. The original
external preregistration and its SHA-256 remain unchanged.
