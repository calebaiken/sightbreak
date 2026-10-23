# Acquisition wrapper source freeze

This is a source/pure wrapper handoff. Runtime is held for fresh independent
review and root's separate release. Accepted candidate source remains
`1b7ebc71290e6c4c23017f7a2d8539d7c5eec149`, reviewed by
`66f31a6778930fb16de41594ec0bd11b7a70189a`. No game, test, policy auditor,
maintained registry, audio, prior evidence or canonical document changes.
Wrapper preregistration is `e1864f3`; the first source savepoint is `3220bef`.

`run_acquisition.py` has two fixed one-shot blocks. Candidate has a 240-second
whole budget and four native stages: producer before, one import, maintained
1,268-row test, and producer after only on strict native and authority success.
Regressions have a separate 480-second whole budget, one import and three
existing suites in fixed order, each with native before/after producer probes
(ten native stages in total). All suite/import caps remain 120 seconds; producer
caps are 30 seconds. Every phase also uses the remaining whole deadline. The
whole clock begins before claiming/staging, with a Linux alarm, and does not
reset for import or regressions. A claim is exclusive per exact HEAD/block in
the own checkout, and changing the output path does not grant a retry.

The reviewed launch templates and exact native argv are in PREREGISTRATION.md.
Replace its single commit placeholder with the final reviewed wrapper commit;
`--expected-head` must be that full hash and match the clean own checkout.
The wrapper also checks accepted game/scripts trees and all accepted candidate
manifest hashes. It never runs `--version`, setup, exports, validate.sh, another
suite, `--observe`, or an adaptive diagnostic. Root must release the candidate
and regression blocks separately; neither automatically starts the other.

The wrapper copies every tracked game file mechanically and checks original
Git blob/SHA-256 identities. Original index/present-sparse-file and all staged
manifests are retained. No project setting changes: Linux XDG data/config/cache
and Android homes are private per suite under the fresh output. The accepted
native `PROBE` literal measures actual engine userdata/project/settings paths;
the controller verifies those paths and rejects pre-existing profile state.
HOME/proxy values are preserved and are not dumped. Private state and generated
UIDs remain retained. An added derived-test UID is classified as preparation
output, with its hash and first observed boundary, while every originally
copied tracked file must stay unchanged. The prepared non-cache set is then
fixed. This does not claim the enlarged source set equals the original set.

Complete stdout/stderr files and hashes are preserved. `native_log.failed()`
classifies all bytes from both streams, including ObjectDB and typed leaked
instance warnings. The classification concatenation is explicitly a derived
log with no cross-stream ordering claim. On any failed producer/import/suite,
source or cleanup check, no later native command starts. A strict candidate
failure may still get one bounded pure all-row audit/compare of its existing
stdout; that can support diagnosis but cannot upgrade the failed acquisition.
The successful candidate path audits its authority output before launching the
after-producer. Existing suites require their exact complete success markers.

Process observation reuses the retained baseline helper functions unchanged.
The wrapper records command/PID/start ticks/PGID/SID, stable observed identities,
UTC/monotonic times, exits, signals and terminal scans. PIDfd signals avoid
signaling a reused PID. If procfs registration/observation fails, the original
child pidfd or Popen-owned unreaped direct child receives bounded cleanup;
that fallback remains a strict failure with the missing evidence visible.
Any forced cleanup, unexpected survivor or cleanup error fails the phase.
Creation/registration runs under blocked termination signals, so a pending
signal is handled after the process is registered for cleanup. The original
failure remains primary if a later receipt/finalization also fails.

The retained helper limit still applies: polling can miss an unobserved child
that escapes/reparents. No arbitrary descendant cleanup is certified. Linux
pidfd availability, actual signal delivery, native producer defaults, generated
UID behavior, import/parser readiness and shutdown are not observed by this
source handoff. Cleanup is capped at five seconds, followed by one five-second
emergency receipt-finalization allowance; no extra native command is permitted
there. Normal work exceeding the whole budget stays failed.

Twenty-five mocked unittest methods pass, with no skips. They launch no child
process or engine, deliver no real signal and compile no GDScript. Controls
cover fixed caps/order; same-HEAD/block claim rejection; UID versus original
source equality; native producer identities/leftovers; strict warning detection;
missing/duplicate regression markers; expired/claim-delayed whole budgets;
normal/failed launch, registration, PIDfd creation, interruption, wait and timeout
paths; PID reuse; early import/candidate/regression stop; source corruption;
authority-audit failure without retry; and preservation of the first failure.
Pure mocked successes are not native acquisition passes. Initial 21-test and
22-test outputs remain retained beside the final 25-test output.

The original baseline and verbose diagnostic stay strict failures. This wrapper
does not fix an audio owner, insert a shutdown delay, suppress warnings, change
the 1,268-row benchmark or qualify any full-match/release gate. Send any later
source-bound raw result, including strict failures and missing phases, to a
fresh independent actual-output critic before root's selection decision.
