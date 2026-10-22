# Independent offline-observer review evidence

This docs-only packet preserves the critic's original brief, report, commands,
independent raw OCR/test outputs, audit scripts and hashes without rewriting the
review after integration. The code verdict applies to the narrow observer
correction. The full Linux journey remains failed; Windows needs a new actual
native journey. The focused local Linux pass ran in the first ordinary stock
match, without settings restart. It establishes no Mac, physical-device,
performance or numeric HUD/authority synchronization acceptance.

Start with [REPORT.md](REPORT.md), [COMMANDS.md](COMMANDS.md) and the original
[BRIEF.md](BRIEF.md). [preservation.json](preservation.json) records exact copied
bytes and references; [review-manifest.json](review-manifest.json) is the original
critic manifest, preserved unchanged. All independent raw text outputs are
included. Source snapshots, state/cache directories, executables and duplicate
builder packets are excluded.

The original review identifies candidate `0a12135`; `focus-audit.json` records
that head. The original final `review-manifest.json` was generated after the
builder's docs-only `4f20125` timing correction. The only `0a12135..4f20125` diff
is four lines in `RESULTS.md`; the game tree and reviewed observer files did not
change. Integration maps the candidate commits to `785ece8`, `176581f` and
`1afbdda`, with that timing correction integrated as `e930ba4`, the base of this
preservation branch. The original report's timing finding is now addressed by
that base commit; its historical text is retained exactly.

Original paths and commands describe the actual review workspace. The two audit
scripts are exact historical copies, including their absolute workspace paths.
The committed packet can be verified portably from any checkout with:

```sh
python docs/reports/gauntlet/m1-offline-flow-observation/independent-review/verify_preservation.py
```

The original builder packets are already committed beside this directory:

| Packet | Existing archive | Existing manifest |
| --- | --- | --- |
| Windows native pixels, original failures, component checks | [evidence-r1.tar.gz](../evidence-r1.tar.gz) | [manifest](../evidence-r1-manifest.json) |
| Failed full Linux journey and export receipts | [evidence-native-r1.tar.gz](../evidence-native-r1.tar.gz) | [manifest](../evidence-native-r1-manifest.json) |
| Actual Linux focus-only run, PNGs, actions and source receipts | [evidence-focus-r1.tar.gz](../evidence-focus-r1.tar.gz) | [manifest](../evidence-focus-r1-manifest.json) |

The two independent altered negative images are byte-identical to
`hud-comparison-r2/removed-ammunition.png` and
`hud-comparison-r2/removed-health.png` in `evidence-r1.tar.gz`. They are referenced
by hash instead of duplicated. `artifact-identity.json` retains the independent
verification of all 216 original builder files and all three archive hashes.

The image/authority limit remains explicit: the focused fresh-movement PNG shows
health 100 while the adjacent authoritative observation reports 82.74397.
Distinct rendered views and monotonic observer frame counters support the
movement claim; those screenshots have no embedded simulation-tick identity.
The full-journey and platform gates require new actual evidence with their
existing assertions and deadlines.
