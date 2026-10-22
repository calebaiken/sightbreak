# M4 stock weapon benchmark

Status: criteria declared; native execution pending the shared engine lane.

The comparison source is `317410aff6f1a85b4f8c1b5b344c7ec50dd363d2`, game tree
`fb6be859e05812d8707be1ef5c6f747d2588c1e9`. The benchmark uses the actual
`SBActor.tick_authority_actions` path and all four definitions in `SBWeapons.DATA`.
It measures simulation ticks, not physical input latency, listening quality,
animation quality or device performance. External-title and human comparisons
remain blocked by unavailable reference media and people/hardware.

Source inspection found existing all-four sustained cadence coverage, but reload
conservation, switch interruption and numerical damage/feedback coverage are
mostly rifle-specific. No supported high-impact product defect has been found.
No weapon rule or feel parameter will change without a baseline counterexample.

## Components and declared gates

1. Cadence: record every emitted shot tick over 1,800 authority ticks at 60 Hz,
   with an explicitly oversized measurement magazine. Automatic weapons use a
   held trigger; semi-automatic weapons use alternating press/release ticks.
   Automatic cumulative shot phase stays within one tick of the data interval.
   Semi-automatic intervals respect the data interval and the sampled trigger
   edges. A continuously held semi-automatic trigger emits one shot.
2. Reload and ammunition: for every weapon, reload from five missing rounds and
   three reserve rounds. The sum of magazine and reserve stays constant on every
   tick; no transfer occurs before completion; the final magazine has two missing
   rounds and zero reserve. Completion is no earlier than the configured reload
   and no later than one physics tick beyond it. Record exact completion ticks.
3. Switch interruption: cancel a reload halfway through with an ordinary owned
   weapon request, return to the original weapon, and verify that magazine and
   reserve are preserved and the cancelled reload does not complete. A ready
   alternate weapon cannot emit a shot before its 0.3-second deploy delay; the
   original weapon's cycle time is retained while holstered.
4. Damage and feedback: fire real rays at isolated enemy body and head volumes,
   recording produced contact distance, damage, shot/ammunition change and
   confirmation flags for every weapon. The recorded distance and stock damage,
   falloff and head multiplier determine expected damage. One accepted hit emits
   one confirmation; misses, friendly obstruction, dry fire, reload and deploy
   cannot emit a damage confirmation. Feedback expiry cannot change authority.

Each component must retain its raw measurements and any failure. A source change
requires a baseline failure, candidate pass, and controls against weakening the
invariant. A fresh critic must inspect frozen source and actual outputs; the
builder cannot approve this work. Whole G4/G5/G6/G9/G18 remain open.

## Execution boundary

The ten-account qualification owns the local engine/render/CPU lane. No Godot,
native capture, renderer or OCR process has been started for this increment.
The root must explicitly release that lane before native execution.
