# Independent Mac ordinary source review

Verdict: **APPROVE SOURCE** at
`bd9ac47b58294440a173548402a19db28ab843b8` for one later bounded ARM Mac
ordinary-component attempt. Native isolation, input and gameplay remain
UNVERIFIED. Root retains control of the single native execution lane.

The largest remaining gap is actual output from the exact exported app: no
reviewed native evidence yet proves that the sibling override establishes private
userdata or that CGEvent input produces the living fire/reload pixels, FIELD
MENU, ordinary leave and clean close within the original budgets.

The implementation was reviewed against preregistration `52871a2`, the existing
Mac menu/input/capture/preflight code, exported-offline observation code and
original stage limits. The initial moving draft was never approved. Candidate
`7f54901` failed independent pure counterexamples: a successful helper wait
returning at 25.001 or 60.001 seconds escaped its stage limit, and a .2-second OS
acknowledgement extended the nominal one-second fire hold to 1.2 seconds. Both
raw failures remain in `logs/`. Frozen `bd9ac47` rejects late helper returns and
uses fixed fire/release slots; R-up acknowledgement also consumes the fixed
reload-completion deadline. Ordinary close has its own post-wait deadline check.

The source inspection found:

- The game tree and original Mac helper, menu, preflight, strict native-log,
  build-manifest and Windows/Linux ordinary controllers are unchanged from
  `52871a2`. The workflow adds 11 lines, with no removed original lines or
  changed host matrices, journey/objective/full-match commands or budgets.
- The controller validates the exact export manifest, copies the app with file
  bytes and modes preserved, adds only the executable-sibling two-setting
  override, records full inventories and executable/PCK/override/helper hashes,
  and checks the original and copied payload again at finalization. Actual
  account HOME, default/private ancestor symlinks, fresh private path and the
  engine-created private log are guarded before Deploy; default bytes/modes
  remain checked through input and finalization. Relevant inherited environment
  values are recorded without a wholesale environment dump.
- Living observations bind the same first player and round, full initial
  sidearm, stock profile/rules, protocol 6 and prediction off. Fire needs
  depletion and two drawn frames; reload needs an observed positive countdown,
  exact ammunition conservation and later frames. Native HUD values must match
  living same-round authority on both sides of capture. Foreign windows,
  malformed chrome/Retina mapping, ambiguous pointer labels, menu overlays,
  dead/spectator/reloading pixels, missing evidence and stale observations fail.
- FIELD MENU must freeze the living authoritative state. LEAVE MATCH uses the
  original native label coordinates; returned home, acknowledged releases,
  public AppKit termination and exit zero are required. Cleanup, fallback
  signals after apparent success, changed source/export/default data and strict
  native error/leak signatures can all overturn completed gameplay.

The upstream `project_settings.cpp`, `SConstruct` and `os_macos.mm` bytes were
independently fetched from the preregistered Godot 4.7.2 URLs and matched their
registered SHA-256 values. The inspected PCK-loading branch loads the executable
sibling `override.cfg`; the template's path-override restriction remains in
force. That source check establishes a plausible route, not actual artifact
capability. Before Deploy the native attempt must prove the private log exists
and the whole default inventory is untouched.

The reviewer extracted frozen source with `git archive`, restored the exact
tracked screen-identity fixtures, and ran the following pure checks. All process
exit codes were recorded explicitly in `builder-controls.json`.

| Check | Result |
| --- | --- |
| Independently authored actual-controller AST falsifiers | 9 groups PASS, 0.162 s |
| Candidate isolation/input helpers | 14 tests PASS |
| Candidate complete mocked controller | 7 groups PASS |
| Original Mac menu | 11 tests PASS |
| Original Mac focus | 9 tests PASS |
| Original Mac screen identity | 7 tests PASS |
| Original read-only Mac preflight | 9 tests PASS |
| Source diff whitespace check | PASS |

The independent suite executes the actual nested controller functions and
finalization block with invented states. It covers late stage success, helper
limits, input slots, stale timestamps, foreign windows, geometry/permission
failures, missing PNG/receipt, living/fire/frame constraints, observed reload
and conservation, authority around HUD capture, surviving groups, fallback
signals, source changes, strict leak detection, release errors and the whole
300-second limit. These are pure falsifiers, never native receipts.

`frozen-source.json` independently records the five candidate file hashes, game
tree, content hash and validation hash. The validation hash is
`4a3a2563c33a4d6b1c3cf1b1e1e4d9b91bec8eaead95cad31448ebcb7a934f15`.
Builder documentation head `c096db3` changes only component reports/logs; its
source/workflow bytes are identical to the reviewed freeze. Any later native
export still needs a clean exact-source manifest for the actual executing HEAD.

No export, engine, Swift compiler, service, CI dispatch or native input operation
was performed by this review. Actual raw screenshots, engine/client/helper logs,
source/export/private/default inventories, event timings, releases and cleanup
receipts require an independent native-output verdict before component acceptance.
Objectives, completed matches, progression restart, Intel, physical devices,
human experience and shipped-title parity remain outside this component.
