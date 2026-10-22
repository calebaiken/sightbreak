# Desktop-base input freshness comparison

The six-line input-stream correction prevents consumed command replays from
renewing authority silence and peer-idle clocks. Separate fresh source and blind
outcome critics prefer the correction, with no observed blocker in this scope.
Initial native Linux measurements meet all eight declared cases; six focused
snapshot-gap repeats also pass unchanged gates and independent review. Aggregate
integration acceptance remains separate. No release or whole G3 acceptance is claimed.

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

## Blind outcome critique and supported iteration

The separate fresh-context `/root/freshness_outcome_critic` inspected only the
anonymous initial packet. It [selected A](OUTCOME_CRITIC.md), independently checking
81 file hashes, 32 logs, 27,874 raw rows and 384 assertions. A meets snapshot-stop
and hostile-replay retirement requirements in both modes; B fails them. Both
labels preserve ordinary input, recovery, shot edges and the declared invariants.
Its [exact task](OUTCOME_CRITIC_BRIEF.txt) and unchanged verdict are retained.

The [mapping](OUTCOME_LABELS.json) is disclosed after that frozen verdict: A is
candidate `8e10df0`; B is baseline `561d0cb`. The initial packet is preserved byte
for byte inside [post-verdict-evidence.tar.gz](post-verdict-evidence.tar.gz), with
its original manifest and separately retained original key. The first evidence
archive remains unchanged. Blinding is partial: launch commands were withheld,
while measured behavioral differences remained visible. The critic could check
internal integrity but could not independently authenticate source launch history
from that anonymous packet alone. Full original receipts remain available.

The critic's largest concern was repeatability: one trial per condition and only
17 ms of margin in the prediction-on stop. In response, three additional native
snapshot-gap trials per prediction mode ran on clean `4bed2f5`. That documentation
head has the identical game tree, driver, probe and engine bytes as measured
candidate `8e10df0`; no runtime code, timing limit or trial condition changed.

| Additional trial | Prediction off stop delay | Prediction on stop delay |
| --- | --- | --- |
| 1 | 0.316 s | 0.332 s |
| 2 | 0.334 s | 0.316 s |
| 3 | 0.333 s | 0.317 s |

All six repeat pairs meet the original 0.350 s stop bound, zero stale-window
movement/speed, 120-command cap, fresh signed recovery, two genuine shot edges,
ammunition conservation, protocol/privacy and clean-exit requirements. The
[supplemental verifier](verify_snapshot_repeats.py) recomputes the
[results](snapshot-repeats-verification.json) from retained raw rows. Including
the two original candidate snapshot cases gives eight observed trials, four per
mode, ranging from 0.316 to 0.334 s, with a smallest observed margin of 16 ms.

The same critic performed a separate, explicitly unblinded [repeat review](OUTCOME_REPEAT_CRITIC.md),
using the [retained follow-up task](OUTCOME_REPEAT_BRIEF.txt). It checked 2,886
authority rows, 2,887 client rows, 12 native logs and 324 raw-data/control assertions.
It independently checked source/test identity and the corrected verifier's fields,
found no blocker, and confirmed that the repeats address the requested same-host
consistency concern. The original blind verdict was not rewritten. The remaining
timing limit is a small sequential sample on one host, with narrow margin and
sampling intervals as large as 40 ms; no failure rate or worst-case guarantee is established.

## Retained failures and limits

- The new stream oracle's two baseline failures and four baseline native outcome
  failures demonstrate the defect. They are not converted into passing results.
- A first local verification of PR20's historical neutral packet failed because
  the extraction directory also contained the downloaded ZIP and output log.
  The verifier correctly rejected extra files. A new clean extraction passes;
  both reports are retained. No upstream packet defect is asserted.
- The first supplemental repeat verifier incorrectly required strictly increasing
  millisecond timestamps. One repeat has two authority clock ties while simulation
  and ACK advance; two other repeats each have one client tie. The original
  comparison allowed nondecreasing clocks. The corrected verifier uses that rule
  and reports ties separately for both roles. The independent critic confirmed
  that ties lie outside measurement/recovery windows and change no selected ACK,
  stop, history-cap or firing event. The failed assumption, first report and
  corrected analysis are retained; no native gate or raw row was changed.
- These are headless, two-peer loopback tests with a collision-only measurement
  platform and suspended bots. They do not establish rendered controls, animation,
  ten-client load, adverse WAN conditions, physical-platform performance or human
  play quality. No CS2 graphical comparison is claimed.
- Source, initial outcome and focused repeat reviews pass their stated scopes.
  Full integrated regressions, ten-client/WAN qualification and product acceptance
  remain separate. These reviews cannot close those gates.

## Evidence and reproduction

Extract [evidence.tar.gz](evidence.tar.gz) into a new directory. It preserves the
complete baseline/candidate summaries, native authority/client rows, logs, metrics,
commands, driver output, targeted negative oracle, initial import, historical
neutral verification reports and source-critic logs. Verify the extracted file
bytes with its `SHA256SUMS`, then run `verify_comparison.py` from the extracted root.
The same verifier and its output are also provided beside this report.

Extract the separate [post-verdict archive](post-verdict-evidence.tar.gz) for the
unchanged initial blind packet, disclosed key, exact outcome-review tasks/reports,
all six supplemental trial receipts/logs, failed verifier assumption and corrected
analysis. Check its `SHA256SUMS`, then run `verify_snapshot_repeats.py` from that
extracted root. The original candidate summary is included so the comparison of
test identities and the eight-trial stopping range can be reproduced.

For a fresh native rerun, import each frozen source, use the identical driver/probe
from `c6690fa`, and write evidence outside either checkout:

```sh
python3 scripts/test_input_freshness.py --godot /workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 --source /path/to/frozen/source --out /path/to/new/evidence --repeats 1 --checks --barrier-control
```

For the candidate add `--expect-fixed`. `--skip-import` was used for the measured
candidate after its separately retained successful import. Use the native pinned
engine for the host. Original Windows evidence is a reference, not certification
of these new desktop-base bytes on Windows.
