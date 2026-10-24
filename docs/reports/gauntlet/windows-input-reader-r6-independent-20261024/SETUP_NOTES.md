# Retained read/setup failures

Before tests: first git-worktree command was invoked from /workspace, which has
no .git. It failed exit128 before mutation. The same setup from the owned
assessment worktree succeeded, populating a full 12,489-path index.

Read-only discovery used guessed game/scripts/net/input_stream.gd and
 game/scripts/match.gd paths; these do not exist (exit1). rg --files established
actual game/scripts/network/input_stream.gd and game/scripts/gameplay/match.gd.
A guessed old controls/fresh_cases.py path also failed exit2; actual retained
control is controls/fresh_controls.py. No source or evidence changed.

The original skill paths were absent physically in /workspace/sightbreak's sparse
view. git show from the owned assessment tree read exact tracked Gauntlet,
no-ai-slop/eval and project skill bytes successfully; no skill was fabricated.
