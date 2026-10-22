# Gauntlet record: Relay Yard layout revision 2

One piece, judged against one bar. Design and measurements: [docs/design/RELAY_YARD_LAYOUT.md](../../../design/RELAY_YARD_LAYOUT.md).

| Item | Value |
| --- | --- |
| Piece | Relay Yard tactical layout and the round pacing it produces |
| Bar | B3: the previous verified build, `codex/desktop-playability-p1` at `db3981e`. Proves improvement. Does **not** prove parity with Counter-Strike 2: the reference hosts are denied here (see `docs/roadmap/BARS.md`). |
| Candidate | Branch `claude/relay-yard-tactical-layout-v1` |
| Environment | Godot 4.7.2 official, Xvfb 1920x1080x24, Mesa llvmpipe, 4 vCPU. Timings are simulation seconds, not frame times. |
| Builder | Claude (lead session) |
| Critics | Four separate subagents, one per round, fresh context each, read-only, blind pairs from `scripts/ab_pair.py` with the key kept outside their reach. Same model family as the builder. |
| Data reviewer | One more subagent recomputed the bot numbers from the raw logs. |
| Exit status | Bar met for improvement: the new layout won the blind overview in every round and won 7, 11, 9 and 9 of 12 eye-level pairs. Absolute quality open: critics scored 5.5, 5, 6 and 6 out of 10, with sites and route structure named as the gaps. Hard-difficulty pacing open. Balance unmeasurable until finding F2 is fixed. No human review. |

## Rounds

| Round | Build seen | Overview | Eye level (new / previous / tie) | Critic score | File |
| --- | --- | --- | --- | --- | --- |
| 1 | v1: screen, exit blocks, site shields | new | 7 / 3 / 2 | 5.5 | [critic-round-1.md](critic-round-1.md) |
| 2 | v2: tags and hardware, dividers, second mid baffle | new | 11 / 1 / 0 | 5 | [critic-round-2.md](critic-round-2.md) |
| 3 | v3 before the last changes: spine extensions, deeper anchors | new | 9 / 2 / 1 | 6 | [critic-round-3.md](critic-round-3.md) |
| 4 | Shipped layout (mid closed, plates sized to text) | new | 9 / 1 / 2 | 6 | [critic-round-4.md](critic-round-4.md) |

Each round's findings changed the build before the next. The loss in round 4 pair 1 is a capture-script bug (camera inside a container), fixed in the frames stored here.

## Files

| Path | What it is |
| --- | --- |
| `critic-round-*.md` | Decoded verdicts, findings that changed the build, abridged reports |
| `stats-review.md` | The independent recomputation of the seeds 31-36 numbers and what it did not support |
| `images/overview-before.jpg`, `overview-after.jpg` | Top-down render. Top of image is the attacker end. Blue = attacker spawns, red = defender spawns, yellow = defender hold positions (each build's own), white = sites. |
| `images/views-before.jpg`, `views-after.jpg` | The same twelve eye-level views, three columns, in the order of `tests/map_viewpoints_capture.gd`. View 01 stands at (0, -17) before and (0, -13) after, because the old mid exit is now solid. |
| `data/bot-summary-before.txt`, `bot-summary-after.txt` | `scripts/summarize_bot_metrics.py --kills` output, seeds 41-46, both start orders |
| `data/bots-before-both-starts-seeds41-46.tar.gz`, `bots-after-both-starts-seeds41-46.tar.gz` | Raw per-match logs behind the headline table |
| `data/bots-before-seeds31-36.tar.gz`, `bots-intermediate-seeds31-36.tar.gz` | The seeds 31-36 runs the data review used: the old build, and the intermediate build in which the mid exit was in the accidental state described in the design document |
| `data/bots-trial-mid-open-*.tar.gz` | The failed attempt to open the mid exit, with and without exit assignment |
| `data/bots-reverse-order-seeds41-48.tar.gz` | Eight matches with actors processed from 10 down to 1 (finding F2) |
| `data/sightlines-base.txt`, `sightlines-final.txt` | `tests/map_sightline_probe.gd` output: exposure map, spawn exposure, route lengths and exposure. The base file comes from an earlier revision of the probe without the route-run lines; the numbers match. |
| `sha256.txt` | Checksums of everything above |

## Limits of this evidence

- Bot-versus-bot simulation on one map. It says nothing about human play.
- The "before" numbers come from the same harness run against `db3981e` with the harness files copied in; the base game files are untouched.
- Critic scores are records, not acceptance. A picture does not override the measured gates.
- The stored log archives are the raw output of the harness; nothing is edited. Seeds 41-46 were not used for tuning. Seeds 31-36 and 11-23 were.
- The attacker win rates in the logs are confounded by finding F2 (actors 1-5 win about 71% of rounds in either role). Read plant rate, round time, first-kill time, kill distance and spawn-zone kills; do not read side balance.
