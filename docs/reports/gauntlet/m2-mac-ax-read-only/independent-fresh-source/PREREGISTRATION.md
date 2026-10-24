# Independent fresh source review registration

Registered 2026-10-23 before reading implementation or running tests. Reviewer
branch `codex/m2-mac-ax-fresh-source-critic` owns this sparse checkout. Handoff
base is `455686ebda9a94326f112319b63f8e5f43ba8c34`; tested source under review
is exactly `cf4de47f5a94e64146dc3f6402da677c41d1b012`. Implementation edits,
nested agents, native/Apple compile, engine/import and CI execution are excluded.
Only source inspection and pure Python controls are authorized.

The concrete comparison is the preserved c838907 ARM run 39920948579 failure:
native and fixed 2× Deploy confidence 0.5, required 0.8, before any CGEvent.
This diagnostic must leave that failed gameplay verdict unchanged. Public
`--accessibility always` and menu initialization of private default profile files
are the explicitly admitted diagnostic-only amendments.

I will reject source readiness if any of these falsifiers holds:

1. Reachable observer/controller/adaptor code can create/post input, request AX
   actions/setters/trust prompts, search globally, inspect another PID/window,
   or read AXValue, text/search/secure-field/account contents. Geometry-only
   AXValue decoding must be distinguished from the forbidden AXValue attribute.
2. The native ABI uses incorrect ctypes widths/signatures/ownership, leaks owned
   CF handles on errors, decodes unchecked foreign types, or lets a hostile
   UTF-8 string/child array bypass declared bounds.
3. The shared native/fake traversal can accept duplicate, spoofed, stale,
   wrong-owner/window/context/geometry/hash receipts, or bypass cumulative 256
   nodes/depth 16/512 KiB/512 title bytes, 0.25 s calls, three snapshots or 5 s.
4. The separate controller changes imported original budgets (whole 300,
   compile 60, window 30, menu 60, focus 5, capture 25, close 20 seconds), starts
   a second focus, repins after identity changes, or accepts late work/failure
   finalization. Failure must retain raw evidence and enforce cleanup and
   source/default/private/payload checks.
5. Game/audio/protocol/economy, raw PNG/Vision data, original 0.8 selector,
   ordinary helpers/controllers, default workflow matrix/steps or normal jobs
   change beyond the explicit new diagnostic choice exclusion. The new choice
   must route solely to its separate ARM diagnostic job and send no Deploy,
   earned-progress or reward action.
6. Maintained pure controls fail in a fresh exact depth-one checkout without
   historical objects. I will independently create that checkout and retain its
   identity, raw test output and failures. Existing passing counts are evidence,
   not proof; I will add independent adversarial pure replays where source
   inspection identifies weak coverage.

Acceptance applies only to exact source readiness. It cannot prove real AX
exposure, TCC trust, C ABI behavior on Apple, native coordinates or completion
within budget. The report will give a binary decision, concrete evidence and
the largest remaining gap; no quality score or native release follows.

Initial setup error retained: looking for the builder registration under
`PREREGISTRATION.md` at 10f16c3 returned `fatal: path
'docs/reports/gauntlet/m2-mac-ax-read-only/PREREGISTRATION.md' does not exist in
'10f16c3'`. Tree listing identified the actual `REGISTRATION.md`, which was
then read. This was a documentation-path error, before code/tests.
