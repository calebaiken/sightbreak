# Fresh R2 actual critic handoff

The actual review is preregistered at `2082e964`, pushed on own branch
`review/linux-profile-acquisition-r2-actual-20261023`. Its parent is the exact
candidate `216d39ada8f9d11e2d8544d01fde42da49607b14`. Own initialized sparse
worktree: `/workspace/reviews/linux-profile-acquisition-r2-native`. Only
`docs/reports/gauntlet/m1-linux-profile-acquisition/native-r2-independent/` changed.

[Conditional admission](ADMISSION.md) accepts source preparation only, with 1,798
passing read-only predicates. The exact candidate and original failed source are
clean; all 430 tracked game/script files in each match frozen Git bytes. The
fresh R2 output/claim and fresh R2 external streams/outer receipt are absent at
the recorded finite observation. No root release is present and no actual R2
engine/import/export/Xvfb/native/profiling/CI work has run in this review.

Root currently owns the heavy lane for the touch replay/archive audit. Keep the
fixed R2 output absent until root explicitly issues ROOT ONE release for the
exact candidate. Then send that real release reference to this critic and ask
it to activate the observer before root launches the one wrapper. The prepared
observer command is:

```sh
cd /workspace/reviews/linux-profile-acquisition-r2-native
taskset -c 4 python3 -B docs/reports/gauntlet/m1-linux-profile-acquisition/native-r2-independent/observe_processes.py --root-release-ref ACTUAL_ROOT_ONE_RELEASE_REFERENCE
```

The placeholder is deliberately not a release. No observer is currently
running. The observer must start before the output exists and writes its
exclusive `live-observer.jsonl` only in this critic's report directory. Confirm
its retained `start` row before the wrapper launch. A rejected or missed
observer launch remains evidence, never an invitation to reuse output or repair
the native acquisition. It automatically stops after the observed supervisor's
ten-second terminal window, or its fixed bounds; it cannot kill a process.

After explicit release and observer readiness, root alone launches the exact
source-accepted held recipe, with no added native command or fallback:

```sh
cd /workspace/sightbreak-linux-profile-fixture-native-types
mkdir -p .local
python3 -B scripts/linux_profile_acquire.py --execute-frozen-source 216d39ada8f9d11e2d8544d01fde42da49607b14 > .local/linux-profile-acquisition-r2-wrapper.stdout 2> .local/linux-profile-acquisition-r2-wrapper.stderr
```

Preserve original initial and terminal tool responses and actual exit in the
new `.local/linux-profile-acquisition-r2-outer-tool-receipt.json`, including true
launch/return time observations where available. A polling duration does not
prove whole wall time. Do not repair, rerun, manually continue, change CPU/display
or start another engine probe after failure. Original five-second cleanup and
ten-second failure publication are evidence preservation bounds; neither extends
the 1,320-second whole acceptance cap or strict phase/condition deadlines.

When the wrapper and observer end, root must separately clear CPU/archive
analysis. The next critic task is actual raw-log, source, compiled import/export,
ELF/PCK/resources, payload/frame/fingerprint, formula/drift, ownership/cleanup,
publication/deadline and complete raw/archive review under [the preregistration](PREREGISTRATION.md).
The strict scanner additionally rejects standalone `Orphan StringName` and
positive `unclaimed string names`; wrapper success cannot override those lines.
Do not infer an H1 result if preparation or any condition is incomplete.

The largest present gap remains actual pinned-engine compilation/import. Original
import failure `f242a2f` and its independent complete 224-file audit `5cbbcd3c`
stay unchanged. Original Linux gameplay failures remain FAILED under every
possible diagnostic outcome. No physical FPS, shipping-performance, complete
profiling-cost, gameplay-cause, optimization or whole-release gate closes here.
