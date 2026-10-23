The first isolated R1 replay loaded the original boundary test from its retained
path in the real worktree. That test inserts a scripts directory computed from
its own path, which selected the current R2 module ahead of the temporary R1
PYTHONPATH. The obsolete read_text hook therefore did not fire, and the runner
stopped at one failure instead of reproducing the two R1 falsifiers. The raw
output and result JSON remain `initial-replay-path-error.*`; they are not a
baseline source result. The runner now loads byte-exact controls from equivalent
paths inside the isolated tree and asserts the imported controller's real path
belongs to that tree. No acquisition source changed for this harness correction.
