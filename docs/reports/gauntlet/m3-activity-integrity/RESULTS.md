# M3 activity provenance

Fresh independent review accepts the bounded correction at product `a9fbdf0`,
subject to root's final combined aggregate validation. G3/G16 remain IN PROGRESS.

The real ENet baseline renewed activity 93 times from an acknowledged command
that the authority discarded. The candidate records zero renewals for the same
traffic while consuming 92 fresh neutral commands. Both builds retain real aim
activity. This fixes the origin of activity observations; actual yaw automation
remains eligible under the existing policy.

## Policy and defect

`docs/network.md:40` explicitly allows validated aim changes. The stock account
run at `471fbd8` therefore does not establish a violation merely because nine
clients turn at spawn. `docs/economy.md:31` and `docs/KNOWN_LIMITATIONS.md:98`
describe basic farming controls and their limits. Meaningful participation,
human identity and automation resistance remain open product work.

The narrower defect crosses an existing authority boundary. Input stream
admission sanitizes each command, discards acknowledged sequences and preserves
the first queued value for an immutable command identity. The original
`_input_rpc` then inspected the received packet's last command independently of
that queue. A packet with a fresh neutral command followed by acknowledged
command 1 carrying an off-angle look passed admission and renewed activity,
although only neutral intent could reach the actor.

Candidate `a9fbdf0c193e327bdd8f8f1d5bf8aaf343b7d8d2` moves the existing activity
predicate to the existing consumed-command branch. Peer input/idle clocks still
use admitted packet receipt; real shot activity still uses the actual shot event.
The fix adds no alive/live, damage, kill, travel or objective-count requirement.
Dead/spectator and buy/post aim keep their current input-activity semantics.
Protocol, snapshot fields, prediction, rewind, account admission, result schemas,
reward amounts and offline/online separation are unchanged.

## Exact sources and native measurements

Criteria were committed before product edits as `cd4c995`. Baseline `e846cd5`
contains the unchanged RPC oracle and its native UID; its `match.gd` is identical
to root `872a576`. The same external driver/probe ran on baseline and candidate.
Both source checkouts were clean and unchanged before/after measurement.

Pinned engine SHA256:
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.

| Actual real ENet case | Baseline | Candidate |
| --- | ---: | ---: |
| Discarded stale-tail activity renewals | 93 | 0 |
| Actual aim changes in stale-tail case | 0 | 0 |
| Fresh neutral ACK advances in observed interval | 93 | 92 |
| Real-look activity renewals | 13 | 13 |
| Actual aim changes in real-look control | 13 | 13 |

All four trials preserve horizontal position, ammunition, no objective progress,
one admitted peer, protocol 6, prediction off and live rewind off. These are
headless guest fixtures on loopback with deterministic geometry and a long live
phase. They assign no account, score, activity, result or reward state and grant
no backend value. They do not replay a full ten-account match, prove WAN behavior,
or measure rendered/device performance.

The clean candidate's focused activity oracle passes 32 checks. It covers
unconsumed/consumed aim, subthreshold aim, neutral intent, stale tails, immutable
duplicates, discarded backlog, epoch and malformed input, dead/buy/post aim,
observed movement, stationary objective holds, ineffective interact requests,
real shots, dry fire, one-delta accounting, the inclusive ten-second boundary,
expiry and terminal stopping. The existing match suite passes 75 checks.

The unchanged prior freshness driver passes all nine focused suites and four
actual ENet cases: steady and snapshot outage, each with prediction off/on.
Authority stops, recovery, genuine semi-auto edges, private state, protocol and
opt-in prediction pass their original gates. No native/resource error appears.
The new activity suite is registered in `scripts/validate.sh`; final combined
aggregate validation belongs to the root integration source.

The separate fresh-context critic independently recomputed the raw pair metrics
and hashes, then ran adversarial native controls for disconnect/rebind queue
cleanup and permanent ranked ineligibility, old epochs, immutable duplicate
ordering, same-packet command semantics, sanitization and intended dead/phase
behavior. [Independent report](independent-critic/REVIEW.md) retains its exact
scope and outputs. Native matrix registration `b166863` is accepted by source
inspection; its combined runner execution remains a root validation step.

## Evidence and reproduction

[raw-evidence.tar.gz](raw-evidence.tar.gz) retains baseline/candidate authority
rows, client observations, metrics, commands, exits, hashes, focused logs and
prior freshness outputs. [raw-manifest.json](raw-manifest.json) enumerates every
file; [archive-sha256.txt](archive-sha256.txt) binds the archive. The initial unit
preflight ran before the candidate commit and is labelled separately; clean
focused receipts supply the final unit evidence. Import-state directories and
engine caches are excluded.
[source-contract-parity.json](source-contract-parity.json) also confirms unchanged
backend/server/network trees and result, shot, ranked-start, disconnect and reset
functions, plus identical product game trees before/after native registration.

Prepare each exact clean checkout with the pinned editor import, then run the
same driver from the candidate checkout against each source:

```sh
python3 scripts/test_activity_provenance.py --godot /path/to/Godot_4.7.2 --source /path/to/baseline --out /path/to/new-baseline-evidence
python3 scripts/test_activity_provenance.py --godot /path/to/Godot_4.7.2 --source /path/to/candidate --out /path/to/new-candidate-evidence --expect-fixed
```

The baseline deliberately fails `activity_gate` and passes the shared controls;
the candidate must pass both. A failing baseline is retained evidence.

The largest remaining economy gap is the participation policy: real repeated
aim changes still qualify. Any stronger rule needs a separately declared policy
and tests that preserve stationary support, objective work and dead-player time.
The known all-match consequence of one inactive participant also remains as
documented; this fix does not change eligibility or payout policy.
