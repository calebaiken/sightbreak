# Retained first handoff and terminal-budget correction

The first handoff was committed as `6ffe3384`. After sending that handoff, I
identified that its loop enforced the 1,200-second limit while the child ran,
but receipt work after a just-before-limit child exit could still mark a result
passed after the declared whole bound. I edited the wrapper to require terminal
`seconds < 1200` before PASS and disclosed that concern to the critic. I should
have sent a new committed handoff before changing the declared frozen file.

The critic's first setup audit correctly rejects the resulting post-handoff
wrapper drift; its failed audit remains retained by the critic. This is a real
source-readiness rejection, with no native or validator execution. Original
`6ffe3384`, its `preparation-r1`/`preparation-r2`, and both earlier pure-control
outputs remain preserved. Narrow correction commit `dc099fd1` adds the terminal
predicate. Fresh `preparation-r3` binds the final wrapper bytes to the same exact
808 runtime inputs, 138 UIDs and pinned engine/archive. No command, game/helper,
fixture, assertion, source gate or budget changes. Native output path `builds/
aggregate-combined-r1` has never been created or consumed. Execution still needs
fresh exact-byte critic acceptance and coordinator release.
