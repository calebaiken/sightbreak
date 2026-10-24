# Independent source verdict

ACCEPT SOURCE ONLY for exact candidate ea6c330a272f17a8a68ef94af868c70bda95a91e, compared with actual baseline 49ae54b0e4f5d880bdf06e4eb783a616b2dff684. The candidate wins the bounded controller comparison. An explicitly supplied callback controls the first displacement, removing the exposed coarse hold while preserving the existing pulse, release, context, stopped-arrival and budget rules. No candidate defect was found by the declared source and pure controls.

Preregistration 3fe7757fbe2df186fae721a93bfb4f9ad478855c precedes detailed source, handoff and output inspection. This is a fresh reviewer verdict, with no score. Source labels were visible because exact implementation and failure provenance were required; this is not a blind visual or shipped-title comparison.

## Original failure and paired reproduction

The original bytes copied from windows-qa-12496379180.zip retain the failed offline-input results and all 190 original actions. Their archive member identities are in originals/archive-member-bindings.json. Actions SHA-256 is af5e69482f2830215e13b33af1e782b14f70b7b5972102b25a46e80e3c7dedac; results SHA-256 is 3306a912b84dce64c36a8368e1ed505dd68e8c65260fe0f9224bc96accc302a4.

Independent extraction confirms the last accepted route sample at tick 3313, x=-8.39777946472168 and vx=-5.09999990463257. Tick 3352 rejects x=-11.5494470596313 for left_declared_clear_corridor. No native pulse was reached. The original failure remains failed; the exact recorded samples and route actions are bound in source-audit.json.

The reviewer authored a separate costed plant using the unchanged 60 Hz motion model, 13-tick publication, and declared .065 s before/after key edges, .070 s per record and .040 s per observation. These are stress conditions, not measured Windows scheduling. Restoring exact original controller bytes in memory makes the supplied-pulse call take the old coarse path, leave the unchanged corridor at x=-9.757777777777795, fail and release all requested keys. The candidate reaches the original stopped endpoint in all nine rate/delivery cells, uses no fallback key-downs and keeps every accepted sample inside the corridor. Maximum modeled wall time is 17.248461538461534 s against the existing 35 s cap. Explicit None follows the original path with identical model receipts, records and key-downs.

## Checks and source scope

Both checkouts pass the same 178 maintained pure methods: 175 pass, with the three existing Windows-only observation skips. The first 14 groups contain 158 methods; the additional native-approach and Mac-menu groups contain 20. Shell syntax passes. The runner is a retained byte-identical command utility; its provenance is recorded. It runs unchanged source tests, with no engine or native helper.

The final reviewer suite passes 14 methods in each checkout. Its 49 malformed/context mutations run at first read, after one pulse, and at arrival, totaling 147 subcases. Additional cases reject a moving or held-input stock start, moving arrival, held-input arrival, duplicate stopped ticks, positive counter regression, context loss on the second stopped arrival sample, late telemetry, unreadability, callback failure/interrupt after down, callback overrun and final logging delay beyond the cap. Every route failure avoids an endpoint and releases requested movement keys. A synthetic low-rate sample sequence verifies the existing 2.5 s callback duration ceiling.

RealKeyPulse cases execute the actual key mapping, _input and key_pulse implementation with mocked User32 and clock calls. Ownership/focus/visibility/thread failures at every read stage reject, including between two downs and after release. External controls remain external. Delayed checks cannot restart the requested hold or create success after the absolute cap. These tests establish fail-closed source semantics, not OS delivery, physical timing or game consumption.

Only scripts/native_approach.py and scripts/test_native_route_pulse.py differ within game/scripts/.github/server/backend scope. The runtime file matches an exact byte transformation: fine = False becomes fine = pulse is not None, plus its explanatory docstring. The entire game, .github, server and backend trees match the actual baseline. verify_offline_export.py, native_settings_route.py, fixtures/export_integration.gd, verify_integration_export.py, validate.sh and build_manifest.py are byte-identical. Their SHA-256 values and Git tree identities are in source-audit.json. The opt-in Windows caller, original endpoint/corridor, schedules, caps and R2 per-down ownership guard therefore remain intact.

The existing route wrapper validates its declared schema, scope, scenario, living actor, round/phase, focus/UI, motion, counters, life/team/weapon/ammunition, ordinary input and corridor fields. Objective metadata and capture-mode metadata are not additional guarantees supplied by this change. The native guard validates its owned visible focused window and control state; it does not read authoritative gameplay context during the physical hold. A newly observed invalid gameplay sample rejects the route after release.

## Initialized shallow reproduction

.local/depth-one-source is independently cloned and populated at exact ea6c330a, shallow=true, commit_count=1 and clean, with no object-store alternates. HEAD^ and the baseline commit object both fail lookup. Its 422 available code/instruction files match the frozen candidate blobs and the own review checkout byte-for-byte. The sparse fixture contains the required source and test paths before execution. Both maintained and independent suites pass there without parent history; the explicit original-controller text fixture belongs to this report. The maintained suite imports no report modules.

The own review branch's maintained replay names preregistration commit 3fe7757f because it is a documentation-only child of the candidate. The source audit proves its populated code bytes match exact ea6c330a. The shallow replay itself names exact ea6c330a. All execution used CPU 4 and pure/source tools. No native workload, CI job or export ran.

## Qualification conditions and largest gap

Root may integrate this exact bounded controller correction while retaining the declared baseline union and unchanged game/guard/schedule/corridor/budget contracts. Any combined source must be checked at its resulting exact identity. A native attempt still requires root's separately preregistered release and an independent actual critic. This report authorizes no dispatch.

The largest remaining gap is actual Windows delivery and successful completion of the living route, settings, LEAVE/reopen and focus journey. The source-only model cannot establish survival or how Windows and the game consume the pulses. This candidate does not address the separate ordinary-input disconnect/reconnect/unbound-actor failure. No product-input fix, network cause, actual living success, physical-device result or whole release gate is qualified.

Reviewer setup mistakes are retained in REVIEWER_SETUP_ERRORS.md and depth-one-setup.log. The initial 10-method pass, expanded 13-method passes and final 14-method passes remain as separate original logs and rows; nothing was overwritten. No candidate test failure was reinterpreted as passing. Writing was checked against the installed No AI Slop eval for specific claims, direct language and preserved uncertainty.

Reproduce from this own review checkout, choosing fresh output locations:

```sh
taskset -c 4 python docs/reports/gauntlet/windows-reload-route-actual-20261023/independent-source/run_maintained_pure.py --source .local/depth-one-source --output .local/recheck-pure
REVIEW_SOURCE="$PWD/.local/depth-one-source" REVIEW_ROWS="$PWD/.local/recheck-rows.json" taskset -c 4 python docs/reports/gauntlet/windows-reload-route-actual-20261023/independent-source/test_independent_controls.py
taskset -c 4 python docs/reports/gauntlet/windows-reload-route-actual-20261023/independent-source/audit_source.py --source . --depth-one .local/depth-one-source --output .local/recheck-source.json
```

The standard whitespace check rejected preserved Windows CRLF data. Its complete reproduced output remains compressed, and the CRLF-aware check passes. The source and evidence manifest was verified separately before final handoff; no original bytes were normalized. See reviewer-whitespace-check.json.
