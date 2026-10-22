# SIGHTBREAK v1.0 acceptance

The existing [G1–G20 acceptance matrix](SIGHTBREAK_V1_PROGRESS.md#acceptance-matrix)
is the single source of gate statuses, evidence, reviewers and next actions. It is
reused rather than duplicated. [The mission](SIGHTBREAK_V1_MISSION.md) defines scope
and dependencies; [NEXT_SESSION](../engineering/NEXT_SESSION.md) identifies the exact resume point.

The mission stays IN PROGRESS until every applicable release-candidate gate is
independently verified on a frozen source-bound candidate. No unresolved P0/P1 is
allowed. Correctness, regression, security and performance requirements are separate
from presentation review. Every applicable quality category must meet the existing
8.5/10 target through defensible independent evaluation; scores alone prove nothing.

Gameplay requires real exported-client controls, objectives, full matches, results
and progression reload. Multiplayer requires ten-client reliability, privacy,
authority and result recovery. Desktop platforms require actual execution and play;
Android/iOS compatibility must be preserved. Packaging must bind artifacts to source
and include a documented Steam staging process. Human experience, physical devices,
signing, credentials and unavailable hosts stay explicitly blocked until observed.
A script, simulated match, software render or successful export cannot silently
satisfy a different gate. No deployment, Steam publication or paid action is implied.

Current bounded evidence includes the independently passing frozen 0527715 aggregate,
fourteen-suite Windows/ARM runs, Windows selected gameplay gates, corrected-activity
ten-account settlement/recovery, backend regression and four-weapon probe. Linux
next-round timing and earlier unexplained Mac strict leaks remain failures. The canonical matrix records their exact sources and reviewers;
none of these increments closes the full release-candidate gates.
