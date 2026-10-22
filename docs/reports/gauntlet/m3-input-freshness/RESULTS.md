# Desktop-base input freshness comparison

The six-line input-stream correction prevents consumed command replays from
renewing authority silence and peer-idle clocks. A fresh source critic prefers
the correction and finds no source blocker. Native Linux measurements meet all
eight declared cases. **Independent native-outcome review and aggregate integration
acceptance remain pending.** No release or whole G3 acceptance is claimed.

## Sources and inspected reference

- Baseline: `561d0cbba651514bfac96c50437a849d65843545`, desktop mission/PR24 base.
- Measured candidate: `8e10df0b6508964fbe67a93629b0aa8b3ac86a00`.
- Declared criteria and shared test fixture: `c6690fa`, [CRITERIA.md](CRITERIA.md).
- Original implementation inspected: [PR20](https://github.com/calebaiken/sightbreak/pull/20), runtime `f3ceaad98e089aa393c7f5fa650a52695094d979`.
- The shared native probe and driver are unchanged copies from PR20 tip
  `0cbc3ae7a9a017aa179eaeff61cf902629de1c0d`; hashes match across both measurements.

The published PR20 neutral packet was also inspected: ZIP SHA-256
`8fb111324051b4bfc590a216ab09c107ef0c10605f755b7e481757d125172112`, manifest
`fe83c4bdcc1ea662f034ff4ebc340a4e115ed27e8a7d404a2aa80175d84146ce`.
Its verifier passes 32 recorded pairs / 64 peer receipts and 22 focused processes.
That is a byte/receipt check of historical Windows evidence, not a new Windows
execution or its outstanding comparison verdict.

## Actual implementation

`SBInputStream.accept` now rejects a validated batch when no command sequence is
newer than its consumed acknowledgement. `_input_rpc` then returns before
refreshing activity, action-silence and peer-idle state. Queued unacknowledged
duplicates remain valid and immutable; a mixed old/new batch still queues the new
input. No game clock, RPC, protocol number, prediction default, privacy schema,
reward rule or backend code changed.

Five added stream checks cover queued duplicates, stale rejection with pending
fresh commands, immutable pending contents/ACK, fully consumed replay rejection
and empty-queue preservation. The identical new 22-check oracle fails baseline
in the two replay-admission cases and passes candidate with zero failures. These
intentional baseline failures are retained.

## Native measurements

Both sources ran sequentially on Linux 6.18.55 x86_64/glibc 2.41, Python 3.12.14,
official Godot `4.7.2.stable.official.ed1daf0bf`. They used the same external probe,
driver and engine bytes, normal engine time, real ENet peers and authority physics.
The four scenarios run with actual default prediction off and explicitly on,
one repetition each: eight pairs per source, 32 peer process exits in total.

| Declared measurement | Desktop baseline | Candidate |
| --- | --- | --- |
| Snapshot-gap authority travel in 3.8–4.8 s window | 1.003009–1.020010 m | 0 m |
| Maximum speed in that window | 1.020 m/s | 0 m/s |
| Stop after last consumed ACK, before snapshots resume | No stop | 0.316 / 0.333 s |
| Hostile replay peer retirement after fresh commands end at 2 s | Still retained after 34 s | 32.040 / 32.032 s |
| Binding/lifecycle/queue/pending-join entries after retirement | Retained | All empty |
| Fresh signed recovery, non-hostile scenarios | Below -0.9 m/s | Below -0.9 m/s |
| Genuine held/released semi-auto edges | Two shots, 15→13 ammunition | Same |
| Protocol / private-field violations / active hit-history frames | 6 / 0 / 0 | Same |
| Declared outcomes met | 4/8; both stale scenarios fail in both modes | 8/8 |
| Original nine focused groups | 1,673 passing assertions | 1,678 passing assertions |

Both source identities remain clean and unchanged before/after measurement. All
32 peer exits and every process in the original nine-group regressions exit 0,
without script/runtime/resource leak errors. The intentional empty-barrier control is exercised by every peer
outside the measurement interval. Controlled movement prediction maximum error
remains 0.075834 m on both sources.

The [comparison verifier](verify_comparison.py) separately recomputes fixed-window
travel, speed, last-ACK/stop delay, recovery direction, actual edge/ammunition
results and lifecycle retirement from original authority rows. Its
[result](comparison-verification.json) is PASS. This is builder verification, not
independent acceptance.

## Independent source critique

The [fresh-context source critic](SOURCE_CRITIC.md) prefers candidate `8e10df0` and
independently passes input stream, peer lifecycle, recipient privacy, movement
prediction, resume-alias and lost-welcome tests. It received no builder outcome
results and found no source blocker. Its exact brief, response and unchanged raw
logs are retained.

Its largest remaining deficiency is prolonged snapshot-loss recovery: a stock
client still reaches the 120-command history cap and has no earlier connected-state
snapshot timeout or improved frozen-state feedback. This change prevents stale
traffic from extending existing expiry; it does not shorten the 30-second policy.
That deficiency remains open for a separate milestone.

## Retained failures and limits

- The new stream oracle's two baseline failures and four baseline native outcome
  failures demonstrate the defect. They are not converted into passing results.
- A first local verification of PR20's historical neutral packet failed because
  the extraction directory also contained the downloaded ZIP and output log.
  The verifier correctly rejected extra files. A new clean extraction passes;
  both reports are retained. No upstream packet defect is asserted.
- These are headless, two-peer loopback tests with a collision-only measurement
  platform and suspended bots. They do not establish rendered controls, animation,
  ten-client load, adverse WAN conditions, physical-platform performance or human
  play quality. No CS2 graphical comparison is claimed.
- Runtime source review has passed; a separate fresh-context outcome critic still
  needs to inspect the actual A/B rows and logs. No builder may close this gate.

## Evidence and reproduction

Extract [evidence.tar.gz](evidence.tar.gz) into a new directory. It preserves the
complete baseline/candidate summaries, native authority/client rows, logs, metrics,
commands, driver output, targeted negative oracle, initial import, historical
neutral verification reports and source-critic logs. Verify the extracted file
bytes with its `SHA256SUMS`, then run `verify_comparison.py` from the extracted root.
The same verifier and its output are also provided beside this report.

For a fresh native rerun, import each frozen source, use the identical driver/probe
from `c6690fa`, and write evidence outside either checkout:

```sh
python3 scripts/test_input_freshness.py --godot /workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 --source /path/to/frozen/source --out /path/to/new/evidence --repeats 1 --checks --barrier-control
```

For the candidate add `--expect-fixed`. `--skip-import` was used for the measured
candidate after its separately retained successful import. Use the native pinned
engine for the host. Original Windows evidence is a reference, not certification
of these new desktop-base bytes on Windows.
