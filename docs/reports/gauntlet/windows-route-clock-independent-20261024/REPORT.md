# Windows route-clock boundary: ACCEPT SOURCE ONLY

Frozen candidate `4cf6ac8e744603ed6af122a362036d276754cc76` wins the supported
source comparison against `7101350e5d0a2f6e4afb9a913b5b1bcf2107857a`. In the same
independent fine-sleeper/coarse-clock model, the old exact helper raises its
premature-boundary exception; the candidate requests only residual waits and
reaches the original fixed boundary. All supported independent checks pass after
explicit adjudication of five retained model-expectation errors. This qualifies
this helper's source boundary correction only.

The largest remaining gap is actual Windows behavior under a new, separately
admitted frozen source. Original run `40083894472` failed before reopened launch
and remains INCONCLUSIVE for reopened shutdown. Run `40080238905` retains its
unresolved three-ObjectDB failure. No native success, historical cause, physical
hold maximum, game consumption, shutdown correction or whole gate follows.

## Independence and registration

The supported thread limit prevented a new reviewer thread. Root explicitly
reused this existing bot-objective reviewer, independent of the Windows builder.
There was no prior Windows implementation context when registration was saved
at 10:32 UTC, before reading builder registration or code. The original external
registration SHA-256 is
`67c3b248eda5cdb5dae7918b5bb3dc38f824f0601258fb34e6b1ecab2f9c504a`;
[PREREGISTRATION.md](PREREGISTRATION.md) preserves those bytes.

New own checkout `/workspace/reviews/windows-route-clock-independent-20261024`,
branch `codex/critic-windows-route-clock-20261024`, starts at the exact frozen
candidate. `bd208eac` commits registration and the initial checkout setup failure.
`df6161f6` registers concrete models before execution; `0d68b551` retains the
first rig; `cc412852` adjudicates its failures before the additive rig;
`83505df3` retains that new rig. Builder registration `e46680e4` and final handoff
`f093d8cb` were read separately. No new independent thread is claimed.

## Source composition and checks

[Independent source union](source-union-final.json) checks all 508 tracked paths
outside `docs/`, including instruction/configuration, workflows, backend, game,
server, scripts and tools. The path set and every mode agree between base and
candidate; 506 blobs are unchanged. The only changed files are
`scripts/verify_integration_export.py` and `scripts/test_native_route_pulse.py`.
Every one of those 508 working files and index identities equals exact candidate
Git bytes/mode/blob in both source views.

Replacing the one `WinUI.key_pulse` method with the exact baseline recovers the
entire old verifier byte for byte. Test changes are additions only. Removing
the two new model/test classes and `math` import recovers the old test AST;
all original test lines remain byte-exact and in order. No other controller,
CLI budget, input mapping, game/UID, workflow, privacy, protocol, authority,
economy or native-log source changed.

| Evidence | Observed result |
| --- | --- |
| First independent rig, retained unchanged | 313 cases, 308 matching expectations, five model-expectation failures; exit 1 |
| Additive independent rig, own view | 350/350 matching expectations, including one exact-old-helper comparison; no candidate counterexample |
| Same additive rig, initialized depth-one view | 350/350 matching expectations; identical helper/source hashes |
| Maintained selection, own view | 194 methods: 191 pass, same three Windows-only skips; all 17 groups and bash syntax pass |
| Maintained pulse methods, depth-one view | All 41 pass |
| Independent composition | All 508 source paths/modes/blobs and working bytes match in both views; helper erasure and original-test preservation pass |

The [own maintained results](own-maintained/results.json) retain each exact
command, source-view HEAD, raw log/hash, method/skip count and exit. Own HEAD
contains report-only commits; the independent union binds executable bytes to
frozen `4cf6ac8e` rather than treating a report HEAD as product source.

The independent rigs compile the exact frozen helper AST with ctypes/time names
and run it only on their own fake User32, key and clock functions. They do not
instantiate native UI, call real input/sleep or use the builder's mocks. Exact
model inputs, events, requests, receipts and outcomes are retained in
`own-models-v2/cases.json` and `depth-models-v2/cases.json`; summaries bind the
helper AST and full verifier SHA-256 values.

Positive phases cover continuous and .001/.015625/.0625/.25-second route clocks,
zero/nonzero/large epochs, four phases and requests through the unchanged 2.5
ceiling. Further cases cover true short returns, dispatch/state costs, unrelated
watchdog epochs, operation-longer-than-pulse allowance, frozen route clocks,
request validation, equality/clipping/oversleep and late release. True decreasing
and NaN/infinite reads at down, sleep return, UP timestamps and final recording
fail; every owned attempt still receives an UP attempt. First observed watchdog
expiry forbids any further DOWN or sleep and requires failed completion.

## Why the source passes

The helper computes `H = min(start + requested, original deadline)` once after
initial neutral-state preflight and before per-key dispatch costs. Residual
requests use that same route clock and are clipped to the remaining independent
watchdog allowance. There is no sliding H, epsilon, sleep floor, arbitrary retry
count, renewed operation budget or increased request cap. Same-clock completion
must reach H, all existing release/state checks must pass, and the final original
operation deadline check must still succeed.

The watchdog compares its own elapsed difference with the original remaining
operation duration. It never compares an independent absolute epoch with H or
the route deadline. Invalid/decreasing samples reject; equal coarse samples are
admitted. Timestamp errors cannot prevent attempted UP calls. Errors and late
completion remain failures even if release calls themselves return. The caller
context/input/visibility/ownership checks are preserved. These source properties
agree with the independent models and maintained tests.

## Retained failures and depth limits

[RIG_ADJUDICATION.md](RIG_ADJUDICATION.md) names the original five failed
expectations and exact original hashes. Three deliberately doubled watchdog
rates assumed a nonpreemptible sleep could not cross the observed elapsed cap;
the helper actually timed out on return and released. Two “always backward”
inputs supplied constant negative initial epochs, with no decreasing transition;
one reached the harness abort limit. The initial 313-case rig/output is unchanged.
The additive rig supplies a valid first sample followed by an actual decrease,
a consistent negative-epoch positive, and explicit release/final-recording
faults. Expiry detection, owned releases and all product gates remain required.
Artificial skew-rate checks establish rejection/accounting, not OS-call timing.

Own sparse materialization initially left selected files absent despite index
initialization; that status and failure are preserved. The separate initialized
source view first failed cone configuration because omitted documentation blobs
were unavailable, then failed its clean-status assertion because five tracked
root files remained absent. Both failures and exact restores remain in
[DEPTH_SETUP_FAILURE.md](DEPTH_SETUP_FAILURE.md) and their raw paths. No test ran
in the incomplete view; later checks use fresh output paths.

[Final depth identity](depth-one-final.json) establishes exact candidate HEAD,
one reachable commit, no remote or object alternate/environment, absent parent
object (exit 128), clean status and a 9,186,110-byte locally transferred pack.
This is a separately initialized history-free source repository, not a network
clone or exported artifact. The independent comparison rig reads a retained old
helper source fixture; it does not need an ancestor object. The ordinary reviewer
worktree shares the original object database and claims no independent history
proof itself. Unrelated omitted documentation blobs are not approved evidence.

## Reproduce and scope

From this reviewer checkout, use a new output directory:

```sh
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/windows-route-clock-independent-20261024/controls/independent_models_v2.py --source . --baseline docs/reports/gauntlet/windows-route-clock-independent-20261024/controls/base-verify_integration_export.py --output /tmp/route-clock-independent-NEW
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/windows-route-clock-independent-20261024/controls/builder_run_pure.py --source . --output /tmp/route-clock-maintained-NEW
taskset -c 4 env PYTHONDONTWRITEBYTECODE=1 python3 docs/reports/gauntlet/windows-route-clock-independent-20261024/controls/verify_source_union.py
```

The preserved original `independent_models.py` still reproduces its five
adjudicated harness failures; it is not silently replaced by the v2 command.
The depth-model command changes only `--source` to the retained depth-one path.

All execution used CPU 4 pure/static checks. The maintained pure macos_menu
regressions are not a Mac artifact/file-handling review. No Godot, native input,
CI, export, process inspection, Mac review or native rerun occurred. The actual
sleep argument, immediate comparison samples, clock phase/resolution and physical
hold were not measured in the failed run; the coarse-clock model does not prove
its cause. Both clocks or an OS call can stall beyond software's control. Root
must retain both original failures and independently admit any future actual run.
