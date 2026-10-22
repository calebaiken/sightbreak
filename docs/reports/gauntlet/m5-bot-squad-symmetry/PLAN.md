# M5 bot squad symmetry: declared qualification

Declared before product changes, 2026-10-22. Baseline is exact root commit
`42ff3dc3d1f52e40da2120b5bcee39a15b86e1ca`, with reviewed phased authority
`f13ed03`. The inspected source bar is Claude PR28 bot-only commit
`0871bc92b014fdb020cb1ac681fe70637f6cf6cd` (Claude, with Claude Sonnet 5.5
co-authorship), on PR28 head `2641ddf`. Its shuffle `6ed3ee0`, tests of that
shuffle, PR26 arena, and published match statistics are outside this adaptation.

## Correctness gates

Run pinned native Godot 4.7.2 headlessly with the real TacticalMatch, RelayYard,
SBActor and `_bot_input` path. Save actual command dictionaries and role/destination
outputs for actor pairs 1/6 through 5/10 at equal poses, seeds, elapsed time and
assigned tactical role. These are deterministic fixtures, not human gameplay.

1. Reproduce baseline unequal crouch and smoke command counts, unstick direction,
   and easy/normal/hard defender destinations. Check every paired slot, rather
   than helper arithmetic or counts alone.
2. Candidate pairs must emit equal habit commands, role and destination, with
   expected positive and negative controls for crouch, smoke, stuck thresholds,
   defender anchors, carrier planting, and defender defuse/cover selection.
3. Preserve all three difficulty profiles, reaction delays, long-range braking,
   utility gates, objective interaction stop, one smoke per round, and the bot
   command-only authority boundary (health/ammo/utility/credits unchanged by a
   decision). Inactive/dead bots remain inert. Protocol stays 6 and offline
   results cannot produce ranked payloads.
4. Run maintained bot AI, match, lifecycle, actor, weapon, hit-volume,
   authority-order, match-objective and state-privacy tests. Register the new
   deterministic suite in maintained validation. Preserve failed iterations.

The source delta leaves raw-ID sine phases in close combat strafe and idle scan.
Before product edits, root authorized extending the adaptation to normalize both
phases to the same squad-position basis. This is our adaptation beyond Claude's
four-rule delta, attributed separately. Full paired command equivalence is now
required across both assigned tactical roles, all five slots, easy/normal/hard,
close combat, long-range combat, idle scan, navigation and objective states.

## Optional bounded observation

Only after the native/CPU lane is released: a fixed matched set of seeds
`[71, 72]`, both initial squads attacking first, normal difficulty, baseline and
candidate, eight complete all-bot engine matches total. Run serially, time scale
4, original round rules and original actor insertion order. A swapped start is
an explicit artificial initial-condition control. Do not use PR28 reverse-order
mode. Record every match, timeout or failure; no sample stopping or replacement.
Record round winners by actual squad IDs, plant count, rounds, kills and elapsed
simulation seconds. This is a small descriptive observation, with no fairness
confidence claim, native human gameplay claim, or earned-progression claim.

The optional set is not required to establish deterministic habit correctness.
Do not interfere with layout timing comparisons. A fresh independent critic must
review exact product and evidence before integration; this builder cannot approve.
