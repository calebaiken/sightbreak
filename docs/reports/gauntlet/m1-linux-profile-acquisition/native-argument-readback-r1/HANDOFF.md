# Native thread readback source handoff

Unreviewed source-only candidate. Implementation commit is
`525b17f17fa8e1d500320198107553b42c9464ea`; the final evidence freeze is the
commit containing this handoff. Preregistration `4554462b` was committed and
pushed before implementation. Own branch is
`codex/linux-native-argument-readback-20261023` in
`/workspace/sightbreak-linux-native-argument-readback`, based on exact
`ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef`. No root, contributor, frozen checkout,
canonical mission, game or native artifacts were edited.

## Preserved failure and inspected source

R3 remains FAILED: one root-released invocation exits 1; the first OFF client
exits 2 before readiness with the original filtered-argument guard error. The
VSync warning independently violates the original strict acquisition gate.
Import/export/artifact/seal passed; no performance condition or H1 completed.
The exact original error, launch, block and outer receipt remain retained here,
with the critic's initial failure packet at `05881df9` / `587b0c74`.
[Preservation](pure-controls/original-preservation-final.json) verifies all 370
original raw identities, the exact file set, original clean HEAD and unchanged
source status. Actual R3 filtered arguments and effective thread state were
never recorded and remain unknown.

The [preregistered bar](PREREGISTRATION.md), [full-source identities](pinned-godot-sources.json)
and [line-numbered excerpts](pinned-godot-excerpts.json) bind exact upstream Godot
`ed1daf0bf001b61586d9930840f2f1394092c079`. `main.cpp` consumes `--render-thread`
without including it in the list returned by `OS.get_cmdline_args()`. The pinned
public RenderingServer and OS bindings provide effective main/render caller
identity. This source-derived explanation is separate from unretained actual
R3 readbacks.

## Bounded correction

The unshipped diagnostic requires both main-caller identity and
`RenderingServer.is_on_render_thread()` before constructing the workload. Its
existing settings observations retain both actual booleans; the evaluator
requires real `true` values, rejecting false/missing/numeric/string substitutes.
It retains the filtered engine argument list as a readback without interpreting
that list as full process argv. The old constant `thread_mode_argument` is removed.

The controller still verifies exact launch, affinity-launch and actual full argv,
including one pre-separator `--render-thread safe`. This independent intent check
rejects `separate`, missing/reordered/duplicated/post-separator flags and deprecated
`unsafe`, which Godot internally maps to the same synchronous state. Project
thread model 1 remains required. Only changed controller/fixture hashes and the
fresh R4 output path change in the supervisor; every supervisor function remains
unchanged.

[Source audit](audit_source.py) verifies exact bounded fixture replacements, only
`validate_condition` changed in controller function/class ASTs, all acquisition
function/class ASTs unchanged, and 488 of 493 existing non-document files unchanged.
The five changed existing paths are the diagnostic, controller, supervisor and
two synthetic test files; one new pure test file is added. All shipping game bytes,
graphics, CPUs 0/1, LP 2, display 99127, selectors, source/cache/payload bindings,
OFF/ON/ON/OFF, 32+64 samples, 180-second conditions, phase caps, 1,320-second whole
cap, formulas and strict log gates remain unchanged.

## Pure results and retained failed checks

Own checkout and a newly initialized depth-one checkout each pass 38 acquisition,
22 fixture/controller and 9 readback methods, with no skips. New controls bind the
actual retained bytes, reproduce the old guard failure through an explicitly
labeled pinned-parser model, verify new effective-state and separate exact-argv
requirements, and inject the exact original VSync warning into otherwise valid
bound synthetic output. The real outer `Acquisition.run_block()` rejects it.

The first new test run wrongly assumed the standalone error/leak matcher scanned
warnings. That failed assertion is retained, and the corrected test verifies the
unchanged outer strict gate. The first source audit omitted a tracked `.github`
file in sparse checkout; the original error and exact restoration are retained.
The first depth-one fetch used an abbreviated object name and failed before
checkout; a full-SHA fetch succeeded. Each setup note distinguishes failure from
the later passing invocation. None caused a native retry.

The fresh checkout `/workspace/fixtures/linux-native-thread-readback-depth-one`
is exactly implementation commit `525b17f1`, one reachable commit, shallow=true,
clean, and has no original base commit object. All checks ran on CPU 4. Commands:

```sh
taskset -c 4 python3 -B -m unittest discover -s scripts -p 'test_linux_profile_acquire*.py' -v
taskset -c 4 python3 -B -m unittest discover -s scripts -p test_linux_profile_overhead.py -v
taskset -c 4 python3 -B -m unittest discover -s scripts -p test_linux_profile_thread_readback.py -v
taskset -c 4 python3 -B docs/reports/gauntlet/m1-linux-profile-acquisition/native-argument-readback-r1/audit_source.py
```

Own and depth-one outputs are retained in `pure-controls/`. No native compilation,
Godot/version/import/export/render/Xvfb/profile/CI/dispatch ran for this candidate.
The builder cannot approve its source or authorize a run. Fresh source critique
is required; exact-source actual admission and explicit root release remain
separate conditions. No available agent slot was free for nested delegation.

## Native execution remains held

Pinned GLX source warns whenever all three swap-control extensions are absent,
then returns before changing `use_vsync`. X11 creation calls it for either VSync
mode, so adding `--disable-vsync` does not supply a faithful warning correction.
The original warning proves this failure path occurred in R3; no supported
resolution under the unchanged software-driver setup has been established.
No driver, graphics, VSync, pacing or warning-filter change is proposed.

The largest remaining gap is strict software-driver qualification plus actual
native evidence of the new effective thread readback. A new acquisition in the
unchanged warning-producing setup is not justified. R4 output remains absent;
there is no release recipe or request here. This candidate preserves a valid
source correction for independent review while the native method and H1 remain
unqualified.
