# Independent native-suite registration review

**Source accepted** at clean
`fb059e470f292aa9ecb0502ab1d127384c9e001d`, based on
`ecc2690dc783a3243291f8ac3438d44fe0151117`. Preregistered criteria are
`5e18bea`. The only code change is `scripts/run_native_regressions.py`.
Runner SHA256 is
`4d13e981f9a16581ba8247028dc3688f06db814e357b1a0b346257b13e93f5af`.

The original **12** suite identifiers and their order remain unchanged:
actor, match, authority_order, state_privacy, movement_prediction, peer_lifecycle,
input_mode, menu_focus, offline_diagnostics, hud_objective_hint,
activity_provenance and bot_squad_symmetry. The proposed default and CLI list
has **14**, appending transaction_journal and gunplay_rules in that order.
Earlier actual 12-suite results remain 12-suite results.

I independently exercised the real `NativeSceneSuites.run()` selection path
with native entrypoints replaced by mocks. All original 12 still receive the
exact original `--headless --script res://tests/<suite>_test.gd` argv and a
120-second timeout. Journal receives
`--headless --script res://tests/transaction_journal_test.gd`. The sole explicit
exception is gunplay:
`--headless --audio-driver Dummy --script res://tests/gunplay_rules_probe.gd`.
No other suite receives an audio-driver override. Both selected scripts exist
and match the accepted validator invocations.

Independent controls also verify default CLI selection of all 14, explicit
selection/order, duplicate/unknown CLI rejection before context construction,
five unknown identifiers rejected before configuration/probing, stale-save
rejection before execution, and retention of results/user data when a process
fails or the strict log gate rejects it. Actual normal/failure `run()` paths use
the same after-producer receipt, inventory and preservation code.

Every runner method except the small `run()` argv-selection edit is AST-identical
to the inspected base. Raw diff review confirms the strict `native_log.failed`
gate, source/copied-resource inventories, unique private project and user
namespace, native producer receipts, 120-second suite/30-second producer limits
and owned cleanup remain unchanged. Game/backend/server/workflow trees and
toolchain, warning parser, diagnostics, validator and existing test files are
byte-identical. The candidate remains clean after this review.

I independently reran the 14 existing diagnostic unit methods and 24 existing
manifest/native-log unit methods; all pass. Their expected fake timeout and
rejection outputs remain in the raw logs. These counts describe Python unit
methods, separately from the proposed 14 native suite identifiers. No engine,
renderer, OCR, service or CI process was launched by this reviewer or builder.
There is no blind visual comparison for this source registration.

Evidence: [source-audit.json](source-audit.json),
[command-controls.json](command-controls.json), rerunnable
[check_commands.py](check_commands.py), and the two retained pure-control logs.

The largest remaining gap is actual native execution on the integrated source.
This review does not establish completion of the new 14-suite default, execution
of either added suite on Windows/ARM, repair of any earlier strict leak failure,
exported-player behavior or whole release-gate acceptance. Root owns focused
private Linux execution, its full aggregate and subsequent actual native lanes.
