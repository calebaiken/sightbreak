# Intel macOS render attribution

The product gate remains the unchanged exported game, default graphics, with a
120-second graphical budget and a captured menu. A diagnostic pass cannot close
G13, verify gameplay, establish physical-GPU performance or establish CS2 parity.

The inspected reference is the actual pinned Godot 4.7.2 native minimal control
and frozen/current SIGHTBREAK exports in Actions run 39712752860, Intel artifact
12398461742. The original artifact is retained here with SHA-256. The measurable
comparison is native completed-draw progress on the same host and budget. There
is no subjective visual or shipped-title comparison in this round.

A candidate may change shipping graphics only after evidence identifies the
responsible work and a separate critic reviews the correction. Stripped sample
stacks currently locate CPU fragment execution but do not identify the material,
shadow or sky pass. This round adds controlled diagnostic feature cases.

The diagnostic must:

- Copy tracked game resources into a fresh fixture outside game/ and the shipping
  payload; preserve the source and shipping receipt.
- Export the full menu as a Universal 2 diagnostic with the pinned engine.
- Keep a full feature reference and change one named feature group per case.
  All cases use one fixed initial menu camera, viewport, UI and geometry.
- Trace each completed draw, capture after exactly 15 completed draws, retain
  failed trials and native samples at 15/90 seconds, and keep the 120-second limit.
- Reject an exit marker alone, incomplete/duplicate/wrong-case frame traces,
  regressing timestamps, dirty logs or missing captures.
- Pass exported Linux fixture correctness controls and trace-validation tests.
  Linux software-render timing is never Mac evidence.
- Receive independent review before a Mac CI dispatch. Builder self-review does
  not approve this candidate or any product acceptance gate.
