# Common-fixture baseline

The unchanged product source at `b0635964c6b819ed41a9568afdb0b5068c3d5577`
ran once after independent source approval `d5df016`. The registered fixture was
unchanged, SHA-256
`059a49bdf1e755a049e0fa4a904d303eb5fc9ce1fd05cbfc993ee9881aa46863`.

The actual Godot 4.7.2 run exited 1 after 1.269 seconds, within its 120-second
bound. All 84 cases, 48 sequence steps and 590 checks completed. Forty registered
expectations failed: 21 primary requests, three reload expectations coupled to
those primary requests, and 16 sequence predicates. No engine error was emitted.
This intentional baseline failure is retained, not reclassified as a pass.

| Profile | Sequence | Switches | Dry equips | Empty reload requests | Shots |
| --- | --- | ---: | ---: | ---: | ---: |
| Easy | No target | 1 | 1 | 7 | 0 |
| Normal | No target | 1 | 1 | 7 | 0 |
| Hard | No target | 1 | 1 | 7 | 0 |
| Easy | Alternating visibility | 1 | 1 | 7 | 0 |
| Normal | Alternating visibility | 8 | 4 | 0 | 0 |
| Hard | Alternating visibility | 8 | 4 | 0 | 0 |

These outputs demonstrate a bounded defect in the actual decision and authority
consumer: a sidearm holder selects a recorded dry primary, then either keeps
requesting a reload that cannot start or repeatedly equips the sidearm and dry
primary as visibility changes. They justify the registered primary-return guard.
They do not identify the cause of a historical full-journey failure.

The private state path, exact command, observed PID/session/start tick, source
hashes, actual exit and cleanup are in `baseline-r1/receipt.json`. Both process
tables contain no engine before or after the run. No same-session process or
recognized Godot process remained in the terminal scan; no cleanup signal was
needed. The source snapshots match. Raw output SHA-256 is
`54982dfa591dbdaa5d213d4b0f53040dc6aa657e9a9d20813a3405c210298347`.

The fresh critic identified limits in the common fixture before runtime. Raw JSON
does not contain every protected snapshot or input inventory/store, so deep
authority comparisons rely on the retained reviewed fixture assertions. The
matrix omits all-three-loaded and dry-rifle/dry-marksman/usable-SMG priority
cases. The candidate must preserve the literal priority list. Visibility is
injected, and the interaction checks are narrow controls. These outputs establish
neither complete perception/objective coverage nor full-match bot quality.

The controller enumerates session membership, not recursive PID ancestry. It
does not qualify escaped-descendant discovery or timeout/failure cleanup. Its
actual normal-exit evidence covers one observed engine PID and the terminal
session/recognized-engine scan.

Product code is still unchanged at this baseline checkpoint. The next permitted
product delta is the registered skip of a known holstered `(0, 0)` primary.
