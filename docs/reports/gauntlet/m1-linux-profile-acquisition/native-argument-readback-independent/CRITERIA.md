# Independent effective-thread source review criteria

Recorded 2026-10-23T12:05:40.631358+00:00 before candidate code, handoff or test-output inspection. Reviewer owns `/workspace/reviews/linux-effective-thread-fresh-source`, branch `codex/critic-linux-effective-thread-source-20261023`. Exact candidate is `93f32edf563c74e250a95505630d4b7870722c78`; implementation `525b17f17fa8e1d500320198107553b42c9464ea`; builder preregistration `4554462b`; baseline `ec6b34ce9af4db1199cd5266b2f7cfcc9831f5ef`.

The named comparison is the actual R3 failure and the independently obtained pinned Godot `ed1daf0` startup/rendering API implementation. This is an asymmetric source correction comparison; blind A/B would hide the required semantic evidence. No visual or runtime winner can follow.

Acceptance requires all of the following:

- Independently establish public pinned API existence, script binding and semantics. Determine whether strict boolean main/render-context readings really identify the required synchronous renderer mode; distinguish launch intent, effective runtime state and absent historic readback.
- Inspect every changed non-document path and source inventory. Preserve effective-render/VSync rejection and all strict warning checks; reject missing, wrong-type and inconsistent diagnostic inputs. Check launch intent is explicit before the user-argument separator and is retained independently from filtered script arguments.
- Run meaningful maintained source/pure controls and independent adversarial controls on CPU4 in both the owned checkout and an initialized exact depth-one checkout. Retain any failures with cause and subsequent outcomes. Do not execute Godot, native/import/export/render, CI or observer work.
- Recompute candidate pins, fixture hashes and fresh r4 identities. Audit full non-doc/protected path union against baseline. Preserve every cap, selector, formula, graphics setting, CPUs0,1/LP2/display99127, 1320s whole/phase and 180s condition budgets, and OFF/ON/ON/OFF design.
- Independently verify all 370 prior raw files remain unchanged against retained source-bound records; preserve R1/R2/R3 failures and every missing-state limitation.
- Preserve the VSync WARNING as a strict environment blocker. No suppression, new native recipe, root release, H1/performance optimism or retrospective historic pass is permitted.

Final report must state independent verdict, winner, why and largest gap, without scores. Source acceptance must explicitly leave effective runtime verification open. Only files under this independent report directory will be edited or committed.
