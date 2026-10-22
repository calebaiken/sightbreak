# Independent M4 native review

Verdict: **ACCEPT the bounded stock-rules measurement and the matching maintained
test registration**. This establishes test coverage and observed rule behavior;
no shipping gameplay defect, correction or feel improvement is established.

Measured source is `fc5d677396930f1e84523b3726525dcbf6ea6b83`, game tree
`41abd17652a89c554463faa5b216a7af59aec0e7`. The only change from source-reviewed
`d1e89ed` is `game/tests/gunplay_rules_probe.gd.uid` containing
`uid://cakg78qe7a0d0`, committed after import and before measured runs. All actor,
weapons, match and probe code is identical to the reviewed source. All 309 tracked
game files match the clean measurement-before and source-after receipts; they
were independently rehashed before the builder's evidence commit.

`audit_native.py` reads the actual logs rather than `case-summary.json`. It
records 5,121 passing independent checks and no failures in `native-audit.json`.
All 52 unique case keys exist, exactly 13 per weapon. `native-raw.tar.gz` retains
the original seven logs, launch/result receipts, source receipts, cleanup and
runner script. Every retained input also matches the bytes committed by the
builder under `native-round-2` in `26871f7`. The original rejected probe, source
review and false-acceptance examples remain preserved.

## Actual results

| Weapon | Shots / last tick in 0–1799 | Automatic maximum phase error | Reload ticks / seconds | Alternate first shot after switch | Reported round-trip shot gap |
| --- | --- | --- | --- | --- | --- |
| Kestrel 9 | 129 / 1792 | Semi; 14-tick gaps | 88 / 1.466667 | 18 ticks | 21 ticks |
| Vectorline | 353 / 1796 | 0.015 s | 112 / 1.866667 | 18 ticks | 21 ticks |
| Relay AR | 286 / 1796 | 0.015 s | 136 / 2.266667 | 18 ticks | 21 ticks |
| Longwatch | 36 / 1750 | Semi; 50-tick gaps | 169 / 2.816667 | 18 ticks | 51 ticks |

Every emitted cadence tick matches the independent exact-rational schedule;
remaining ammunition equals 10,000 minus the count. Finite magazines emit the
stock magazine count for automatic weapons and one shot for held semi-automatic
triggers, with zero reserve and no created ammunition.

The 509 partial-reload samples conserve magazine plus reserve on every tick and
transfer the available three rounds only at completion. All durations fall within
the predeclared configured duration through one tick later. The 1,377 cancellation,
deploy and return samples preserve the original magazine/reserve, including while
holstered and for 240 ticks after return. The initial switch/fire action is
retained and emits nothing; no forbidden deploy tick consumes a round. Alternate
shots consume exactly one round each. The marksman's 51-tick round-trip gap
respects its 0.82-second old cycle; the other stock cycles are shorter than deploy
and cannot be distinguished independently through that shot gap.

| Weapon | Actual body health lost | Actual full-health head health lost | Five-health lethal-body loss |
| --- | ---: | ---: | ---: |
| Kestrel 9 | 26.521994 | 87.464046 | 5 |
| Vectorline | 21.442896 | 66.410339 | 5 |
| Relay AR | 34.752195 | 100 | 5 |
| Longwatch | 73.816660 | 100 | 5 |

The twelve positive records contain actual emitted ray origin/direction and
impact position, plus victim and shooter snapshots before and after the shot.
An independent capsule/ellipsoid boundary calculation reconstructs the front
body/head contact and classification within the probe's 0.00001 tolerance. Stock
distance falloff and head multiplier reproduce the recorded damage, capped by
existing health; actual health loss and alive/lethal state agree. Each actual
hit starts the 0.18-second feedback timer with matching flags, and expiry records
zero. Every weapon exercises a real lethal body ray from five starting health.

All twenty negative cases have zero damage events and confirmations. Misses and
friendly obstruction consume one round; dry fire, reload and deploy consume none.
For every friendly case, the independently reconstructed ray reaches both front
and rear actors, the actual impact is at the front friendly volume, and both
recorded health values remain 100. This tests obstruction, rather than absence of
an enemy contact opportunity.

## Provenance and maintained controls

Actual engine version output is `4.7.2.stable.official.ed1daf0bf`. The measured
binary SHA256 is `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
The installed archive's SHA512 matches the pinned toolchain, and its executable
bytes match that binary hash. No engine was launched by this independent review.

The seven launches are sequential, use the pinned wrapper/binary and private
state, retain separate process groups and real exit statuses, and have no engine
error, warning or leak lines. All exit zero without timeout. Actual summaries are
probe 2,840, actor 73, weapon integrity 28, feedback 10 and phased authority 178
checks, each with zero failures. The cleanup receipt covers all seven groups; an
independent live `/proc` inspection finds none remaining. No service or port was
started by the benchmark.

`26871f76dafb30854294e09d6377340a631fa0da` retains the same measured game tree
and adds exactly one line to `scripts/validate.sh`, immediately after weapon
integrity. Its headless/Dummy/probe arguments exactly match the actual measured
invocation; an independent `bash -n` passes. That registration is accepted. The
complete modified validation script and any later combined-source aggregate have
not been executed by this measurement and receive no aggregate-pass claim.

## Limits

Post-visual authority noninterference is supported by the executed inline
snapshot assertion and recorded comparison boolean. Separate raw post-visual
snapshots are absent, so that comparison cannot be reconstructed independently.
Switch-cycle output records the gap rather than both original shot timestamps;
the audit checks the reported gap against stock timing. Negative health is
explicitly recorded for friendly obstruction; the other negative cases retain
counts/ammunition and the executed source assertions.

This is a standalone 60 Hz authority-action rules benchmark, using physics world
obstruction and analytic operator volumes. It does not establish played gunfeel,
physical input latency, renderer/device performance, animation, audio/listening,
human preference or CS2 parity. Existing focused controls pass, but no whole
G4/G5/G6/G9/G18 gate or new aggregate is closed. Protocol 6, phased match combat,
recipient privacy, earned-only economy, opt-in prediction and disabled live
rewind remain unchanged by this test-only increment.
