# Independent S12 Linux offline evidence audit

The retained native run supports the reported Linux offline flow pass at commit `e3c1194a9c7bb2ff8a5e3b81ab122513dce4a32c`. No new blocking source or evidence defect was found in the requested focus/settings scope. The reviewer read the source, recomputed the retained observations, and inspected raw native captures; the reviewer launched no game or engine and changed no repository source.

The run used Godot `4.7.2.stable.official.ed1daf0bf`, Linux x86_64, Xvfb and Mesa llvmpipe. Both actual application processes and Xvfb exited 0; total controller time was 138.679 seconds, with no recorded teardown errors. Both app logs retain the graphics driver's unsupported VSync warning. This is automated native OS input and software rendering, with no physical-device, real-time performance, audio, accessibility or desktop-session acceptance implied.

## Focus and native input

The actual X11 diagnostics independently report W and left mouse button down while the game acknowledges nonzero movement and fire at simulation tick 922. XSetInputFocus changes foreground window from the actual game window 4194307 to root window 543; the game reports unfocused, paused and visible pointer at tick 928. Restoration returns actual foreground focus while remaining paused. Lost/restored observations have identical simulation tick, elapsed time and actor state, demonstrating that held commands do not advance the paused simulation. The read-only `local_input` snapshot still contains the last pre-pause command; it must not be described as already cleared while paused.

A recorded native Escape down/up explicitly resumes. Three later observations, at ticks 963, 976 and 989, retain the same living actor, live round 1, time scale 1, sidearm 14/60 and look angles. XQueryKeymap/XQueryPointer still report W and left mouse button held, while actual game movement/fire/reload/interact commands are neutral. Position is identical across these three observations, with zero velocity. The initial residual movement from restored position to the settled samples is 0.422224 m, consistent with the ordinary velocity present at pause; the evidence supports suppression of newly held input, not a promise of zero inertia displacement.

After OS key/button release, the recorded game command is neutral. A fresh W press produces nonzero actual movement and 0.217779 m authoritative displacement over 13 simulation ticks, without another shot. These states all retain the same living actor and round. Raw `11a` visibly shows the paused Field Menu; `11b` and `11c` show active first-person gameplay with 100 health and sidearm 14/60. They agree with the corresponding native/state sequence.

## Settings and persistence

Raw `07b` and `07c` visibly show mouse sensitivity change from 0.0028 to 0.0051 through the actual settings slider. The reopened process's initial event declares an ordinary stock-spawn match with a fresh random seed and its full loaded `initial_profile` equals the final on-disk saved profile, including sensitivity 0.0051. This proves a runtime load in addition to disk preservation. The remaining training record stays at matches 0, history empty, XP 0 and Credits 0 after leaving both incomplete matches.

`10-reopened-loaded-settings.png` still displays the menu while the newly created match is beginning. It is insufficient visual evidence of loaded settings; the actual runtime profile observation supplies that proof. This limitation does not invalidate persistence or the later fully active focus test. Objective completion and full-match exactly-once reward qualification remain separate gates.

The retained reload observations also agree with the rendered sidearm change from 14/60 to 15/59, a positive reload countdown and elapsed simulation advancement. This is corroboration of this run, not a substitute for other regression gates.

## Evidence

`independent-qa-r12-offline-audit.json` contains the exact source binding, raw capture hashes and 51 recomputed assertions, all passing. Original evidence remains in `linux-offline-r12/`, including results, native action/OS-state log, both app logs, raw captures, initial/reopened trace events and the saved profile. No historical failure was replaced or deleted.
