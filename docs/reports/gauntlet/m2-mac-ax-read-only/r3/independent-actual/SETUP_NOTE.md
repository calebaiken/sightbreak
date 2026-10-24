# Retained local setup observation

The new worktree was created with `git worktree add --no-checkout` at exact
`4854aed946d25d27482af66c332f84aa51cea8fb`. I initially ran sparse selection and
`git checkout-index -a` before populating the new empty index. `git status`
therefore showed the tracked paths as staged deletions. No deletion was committed
and no existing worktree or source branch was changed.

I corrected this own new checkout with `git read-tree HEAD`,
`git sparse-checkout reapply`, and `git checkout-index -a`. The subsequent
`git status --short --untracked-files=no` and later full `git status --porcelain=v1`
were empty; HEAD remained the exact proposed source. This was a retained review
setup failure and no native/test outcome came from the incomplete checkout.
