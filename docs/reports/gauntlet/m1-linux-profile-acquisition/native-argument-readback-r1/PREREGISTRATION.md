# Native argument and render-thread readback correction

Preregistered 2026-10-23 before implementation. Builder branch
`codex/linux-native-argument-readback-20261023`, isolated checkout
`/workspace/sightbreak-linux-native-argument-readback`, exact base
`ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef`. Original checkout, R3 raw output,
and all prior failures remain unchanged. No canonical mission files change.

## Inspected comparison bar

The real failed acquisition is the single root release
`801e4514ab869ad6869e5631dc303f58ca28772f`: one invocation at the tool-clock
observation 11:50:35 UTC, terminal exit 1 observed 11:51:07 UTC. The R3 critic's
immutable early packet is `05881df9` plus `587b0c74` (four initially ignored log
copies are force-added). Copies of its readback, initial failure, and 370-file
registry are retained here. `retained-r3-identities.json` binds copied original
launch, client log, block, outer receipt and original fixture bytes.

Import/export/artifact/seal pass in the recorded phase receipts. The accepted
block exits 1. First OFF exits 2 before `ready.json`, with the exact argument
guard error at original fixture line 270. Launch contains `--render-thread safe`
before `--`. The actual `OS.get_cmdline_args()` return and effective engine thread
state were not retained. No condition completed; no cold/warm/measured samples,
ON/ON/OFF or H1 result exists. The original VSync warning also fails strict logs.

The source bar is upstream Godot
`ed1daf0bf001b61586d9930840f2f1394092c079`, fetched from exact raw GitHub URLs.
Full-file hashes and bounded line-numbered excerpts are retained. `main.cpp`
1570–1597 consumes `--render-thread safe` into `separate_thread_render=0` and does
not append either token to `main_args`. The remaining argument list is stored by
`set_cmdline` at 2250; the exposed binding returns that list. This explains why
the original guard is inconsistent with this pinned parser; it does not invent
an actual R3 readback.

`RenderingServer.is_on_render_thread()` is publicly bound. Default server init
276–289 assigns `Thread::MAIN_ID` when the separate thread is disabled; separate
init assigns the rendering worker's ID in `_assign_mt_ids`. The method compares
the current caller ID with that server ID. Public OS bindings expose caller and
main IDs. Checking both main-caller identity and render-caller identity therefore
establishes synchronous safe state at the observation, while the controller's
exact full argv checks independently preserve explicit safe launch intent.
Deprecated `unsafe` maps to the same state internally, so effective state alone
cannot prove the requested token. The exact external argv requirement remains.

## Proposed bounded correction

Replace only the diagnostic's filtered-argv guard with the public main/render
thread identity checks. Record both boolean readbacks in settings at the existing
observation points. Remove the fabricated constant `thread_mode_argument` from
settings; the exact external argv remains the independent intent evidence.
Require both readbacks to be real booleans `true` in the pure evaluator; retain
project thread model 1 and all existing settings/cadence/source/strict gates.
Retain the filtered engine argument list in the report as a readback, without
treating it as full process argv. Update only the changed fixture/controller
hash pins and select fresh `builds/linux-profile-acquisition-r4` for any later
separately released acquisition. Update synthetic fixture data and add controls.

VSync is a separate retained blocker. Pinned `GLManager_X11::set_use_vsync`
356–375 warns and returns before updating `use_vsync` if all three swap-control
extensions are unavailable. The X11 window creation path invokes it for either
enabled or disabled mode; `--disable-vsync` would still enter this path. This
source-only investigation supplies no faithful warning-removal correction under
the unchanged driver/graphics contract. Do not suppress warnings, change drivers,
change VSync/pacing or reinterpret the warning as passing.

## Measurable gates and exclusions

All work and pure checks use CPU 4. No Godot/version/import/export/render/native
or CI invocation is authorized. Required source-only evidence:

1. Replay the old guard against the retained original launch through a clearly
   labeled pinned-parser model, reproducing rejection because the option is
   consumed. Bind the real old fixture and log error; never call this an actual
   runtime argv readback.
2. Valid synthetic safe/main/render evidence passes. False, missing, numeric,
   string or mismatched readbacks fail. Missing/reordered/duplicated/after-`--`
   safe flags, `separate`, deprecated `unsafe` and project thread changes fail.
3. Original warning/error remain strict failures. Preserved caps, 32+64 samples,
   OFF/ON/ON/OFF, formulas, full graphics, CPUs 0/1, LP 2 and display 99127 remain.
4. Existing focused controller/acquisition/payload controls pass; meaningful new
   controls verify accepted and rejected evidence independently of implementation.
5. A newly initialized depth-1 repository, with no history beyond the candidate,
   runs the same pure checks. All 370 original raw file identities still match.
6. Commit/push bounded source/evidence; fresh independent source critique follows.
   Builder cannot approve. Actual admission and explicit root release must precede
   any new R4 output. VSync strict failure remains open and blocks acceptance.

Largest remaining gap is actual native proof of the corrected readback and a
faithful resolution of the strict VSync warning. Pure results establish neither.
