# Fail closed when owned-process observation is unavailable

Baseb99d2185, exact math kernel/source550e96c9. Root builder owns new branch
codex/fov-math-process-observation-20261024 at
/workspace/sightbreak-fov-math-process-observation. Original runtime/attempt/output,
source550, corpus and588 mathematical rows remain unchanged. Register before edits.
Existing independent math reviewer is reused after actual review; no fresh thread.
No new engine/helper/native/CI/version or acquisition/retry is authorized.

Actual sole attempt after pushed releasea260bfda fails owned native root identity/
session discovery. Complete stdout770593B/stderr0 reach EOF, but no process birth
identity was observed. Current LinuxKernel.children converts missing child-list
files to empty lists; cleanup can therefore claim empty without that capability.
Read-only own-self check286ca8: os_getpid75416 equals /proc/self stat, task75416
exists but children file is absent/FileNotFound. Earlier self check9c4c0a also
fails on missing task75400/children. Neither check creates a child or engine.
This is supported interface evidence, not proof of every cause in the old attempt.

Implement only a source/pure correction: preflight the required current-supervisor
child-list interface before any engine call; missing/unreadable existing task or
parent must fail, never mean empty. Preserve legitimate races only when that exact
task/parent disappeared. Keep existing root/session/executable/affinity/birth and
owned descendant/subreaper requirements. Record intended Popen PID immediately
without delaying stream retention, but do not substitute that integer for verified
birth/ownership. Existing unsupported environment must block before native launch.

Pure tests use temporary proc-shaped files and mocked transitions, never actual
fork/native/helper processes. Cover existing task missing child file; permission/
malformed input; legitimately departed task/parent; multiple threads/duplicates;
empty task directory while parent exists; capability rejection before process
factory; no invented cleanup pass; root intended PID receipt even readback failure.
Retain earlier tests/failures, exact source union and fixed corpus/kernel bytes.
Freeze and independently review before any separately proposed future acquisition.
No new native admission is requested by this correction; old release is consumed.
