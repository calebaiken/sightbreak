# Actual M4 stock-rule measurement

Native checks pass; independent actual-output review is pending. No shipping
rule defect or product correction is established.

The measured source is `fc5d677396930f1e84523b3726525dcbf6ea6b83`, game tree
`41abd17652a89c554463faa5b216a7af59aec0e7`. It adds only the import-generated
probe UID to source-accepted `d1e89ed`; all GDScript and product files match.
The initial clean `d1e89ed` identity, engine/import output, clean measurement
identity and equal final source hashes are retained separately.

Pinned engine is `4.7.2.stable.official.ed1daf0bf`, binary SHA256
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
Each stage has its exact argv, private-state path, PID/process group, timestamps,
wall duration, exit status and raw stdout/stderr. No engine errors or timeouts
were detected. All seven owned native process groups are absent at cleanup.
No external service or shared profile was used.

The probe emits all 52 unique case records, 13 per weapon, and passes 2,840
assertions. Existing controls pass: actor 73, weapon integrity 28, hit feedback
10 and phased authority 178. All 3,129 assertions pass across these five runs;
this is not a full aggregate or a player-experience acceptance.

| Weapon | Shots in 1,800 ticks | Last shot tick | Reload ticks after start | Alternate deploy ticks | Round-trip shot gap ticks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kestrel 9 | 129 | 1792 | 88 | 18 | 21 |
| Vectorline | 353 | 1796 | 112 | 18 | 21 |
| Relay AR | 286 | 1796 | 136 | 18 | 21 |
| Longwatch | 36 | 1750 | 169 | 18 | 51 |

Automatic cumulative shot phase error is at most 0.015 seconds. Alternating
semi-auto presses produce 14-tick sidearm and 50-tick marksman gaps. All four
reload timers complete one tick after their nominal durations, within the
declared bound; this does not justify a feel change. Marksman's cycle is the
stock case distinguishable from the 0.3-second deploy delay.

Raw per-tick reload/cancellation/deploy samples permit recomputation of transfer
and forbidden-window checks. Actual body/head/low-health lethal rays record
health, alive state, emitted damage, contact coordinates, confirmations and
feedback startup/expiry. All four friendly controls hit the front friendly
volume while the enemy behind loses no health. Each dry/reload/deploy control
emits no shot or damage confirmation. Raw post-visual snapshots are represented
by the inline snapshot equality assertion and logged boolean, so that comparison
has less independent detail than the health and ammunition records.

This headless authority-action benchmark measures simulation behavior with an
explicit oversized-magazine cadence fixture and a five-health lethal fixture.
It does not measure physical input-to-fire, human gunfeel, rendered animation,
audio listening, device performance, network recipient behavior or CS2 parity.
Whole G4/G5/G6/G9/G18 remain open. The proposed one-line validate.sh registration
matches the measured invocation and passes bash syntax checking. Its independent
review is pending; no new engine run or broad aggregate followed that line. The
root owns the combined-source aggregate and integration decision.
