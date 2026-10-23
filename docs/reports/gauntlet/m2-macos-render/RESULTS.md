# Intel macOS startup investigation

G13 remains FAILED. No shipping fix is claimed in this round. The concrete
implementation is an isolated exported diagnostic that separates the first
completed draw from the following 14 draws and tests specific renderer features.

## Original native evidence

The retained `intel-original-artifact-12398461742.zip` is byte-for-byte the supplied
Intel Actions artifact from run 39712752860. Its SHA-256 is
`c3179d25d87cce7030bc3d9c9700990094d799eb8610df221e38a8e321b5b8a5`.
The artifact contains full results, logs, captures and 15/90-second sample stacks.
Current source was clean `6a0d8d5d85b4fb37943903886982f51b4ed230b0`, game tree
`13079ab8a3de9b18252a652ed57157e0776cf394`, content SHA-256
`954b0a73cff89483a9270434da7902b2d128f1b9a99c30290dfe03862c038873`.

Pinned Godot reported Apple Software Renderer on macOS 15.7.9 x86_64. Minimal
2D completed in 2.122 seconds, editor minimal 3D in 19.814 seconds and exported
minimal 3D in 6.829 seconds. Frozen and candidate game trials timed out at the
unchanged 120-second limit. The candidate constructed the menu and reached its
first process callback at about 12.2 seconds by default, or about 1.2 seconds
with explicit OpenGL. Neither trial produced the requested capture.

In `candidate-game-default-90s.sample.txt`, the main thread's 1312 samples are all
under `glDrawElementsInstanced_IMM_GL3Exec` and `gleDrawArraysOrElements_ExecCore`.
1275 samples enter `gldRenderFillTriangles`; 1187 reach
`glvmInterpretFPTransformFour` through the software fragment rasterizer. The
15-second sample has the same draw path. The 90-second explicit-OpenGL sample
also spends its main thread in software fragment execution. These stacks show
active rendering work. They do not show a GDScript startup loop, deadlock or
shader compilation as the sampled bottleneck. They cannot identify which
material or render pass produced those fragments.

The old smoke marker is printed after 15 process callbacks. Its absence does
not establish that zero draws completed. That unresolved distinction is why the
new diagnostic traces every `RenderingServer.frame_post_draw` completion.

## Candidate and controls

`scripts/diagnose_macos_render.py` copies tracked shipping resources into a fresh
diagnostic project, adds a wrapper and exports a separate Universal 2 app. Its
user-data directory is separate from the game. The shipping source, exported
payload, graphics defaults and launch verifier are untouched.

Cases are full, shadows off, optional surface detail off, sky subsystem off and
surface textures off. They retain the menu and geometry. Each case reports the
number of changed components; a requested change that touches nothing fails.
The final wrapper freezes the same initial menu camera in every case so elapsed
wall time cannot move a slower case to a different view. These controls locate
work; their simplified graphics are not proposed shipping presets.

Initial exported Linux llvmpipe controls completed all five cases with clean
logs, captures and 15 completed draws each. That first fixture still moved its
camera. Final fixed-camera results are retained separately in `linux-controls.tar.gz`. Timings are retained only as raw
observations; concurrent local rendering and ordered caches prevent a performance
claim. Trace validation rejects missing/duplicate/wrong-case draws, regressing
timestamps and exit markers without draw evidence. Fixture tests also verify
source preservation and separate user data (4 tests pass).

Preserved failed preparation: an initial relative project path was rejected;
initial import found an invalid Environment enum name and the corrected import
passed; an ad hoc Linux export lacked include/exclude filter keys, then passed
with the keys present. A toolchain setup attempt received ETXTBSY because another
agent was executing the shared installed editor. The verified installed 4.7.2
editor was reused, with only local templates extracted afterward. Initial headless
menu-focus/input-mode regressions refused existing local player state with exit 2;
each passed in a fresh per-suite state directory. The earlier explanation that
these tests required a native display was incorrect. World, main, state privacy
and movement prediction regressions also passed with clean logs.

## Next native command

After independent review and a clean source-bound macOS export, run:

```sh
python3 scripts/diagnose_macos_render.py --output builds/desktop-playability/macos-render-features
```

The full feature reference always runs, even when `--cases` selects a subset.
Root owns workflow changes and dispatch. Results must name which cases captured,
which first-draw markers appeared, exact frame times and stack paths. Until that
run, Mac feature attribution is UNVERIFIED. A supported product correction must
follow native evidence and pass the unchanged shipping startup gate afterward.

The largest remaining deficiency is the lack of a Mac feature-attribution run.
ARM startup/controls do not establish Mac gameplay; hardware performance and
CS2 comparison gates remain open.
